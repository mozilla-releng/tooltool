# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64
import collections
import datetime
import hashlib
import json
import os
import random
import time

import boto3
import flask
import moto
import pytest
import requests

# SHA512 digest of "\n"
DIGEST = "be688838ca8686e5c90689bf2ab585cef1137c999b48c70b92f67a5c34dc15697b5d11c982ed6d71be1e1e7f7b4e0733884aa97c3f7a339a8ed03577cf74be09"


def build_header(client_id, ext_data=None):
    """Build a fake Hawk header to share client id & scopes."""

    out = collections.OrderedDict({"id": client_id, "ts": int(time.time()), "nonce": random.randint(0, 100000)})
    if ext_data is not None:
        json_data = json.dumps(ext_data, sort_keys=True).encode("utf-8")
        out["ext"] = base64.b64encode(json_data).decode("utf-8")

    mac_contents = "\n".join(map(str, out.values()))
    out["mac"] = hashlib.sha1(mac_contents.encode("utf-8")).hexdigest()

    parts = map(lambda x: '{}="{}"'.format(*x), out.items())
    return "Hawk {}".format(", ".join(parts))


def test_no_uploads(real_client):
    resp = real_client.get("/upload")
    assert resp.status_code == 400
    resp = real_client.get("/upload?q=abc")
    assert resp.status_code == 200
    assert resp.json == {"result": []}


def test_upload_anon(real_client):
    batch = {
        "message": "upload message",
        "files": {
            "test.txt": {
                "size": 1,
                "digest": DIGEST,
                "algorithm": "sha512",
                "visibility": "public",
            },
        },
    }
    # can't upload without auth
    resp = real_client.post("/upload", json=batch)
    assert resp.status_code == 403


def test_with_scopes(real_client, bucket, mocker, real_app):
    ext_data = {"scopes": ["project:releng:services/tooltool/api/upload/public"]}
    client_id = "test/user@mozilla.com"
    header = build_header(client_id, ext_data)

    batch = {
        "message": "upload message",
        "files": {
            "test.txt": {
                "size": 1,
                "digest": DIGEST,
                "algorithm": "sha512",
                "visibility": "public",
            },
        },
    }
    resp = real_client.post("/upload", json=batch, headers=[("Authorization", header)])
    assert resp.status_code == 200
    put_url = resp.json["result"]["files"]["test.txt"]["put_url"]

    mock = moto.mock_aws()
    with mock:
        resp = requests.put(put_url, b"\n", headers={"Content-Type": "application/octet-stream"})
        assert resp.status_code == 200
        resp = real_client.get(f"/upload/complete/sha512/{DIGEST}")
        assert resp.status_code == 409
        assert "x-retry-after" in resp.headers

        fake_now = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=int(resp.headers["x-retry-after"]))
        mocker.patch("tooltool_api.utils.now", lambda: fake_now)
        resp = real_client.get(f"/upload/complete/sha512/{DIGEST}")
        assert resp.status_code == 202

        runner = real_app.test_cli_runner()
        result = runner.invoke(args="check-pending-uploads")
        assert result.exception is None
        assert f"Upload of {DIGEST} considered valid" in result.output

    resp = real_client.get("/upload?q=message")
    assert resp.status_code == 200
    assert len(resp.json["result"]) == 1, resp.json["result"]

    batch = resp.json["result"][0]["id"]
    batch_resp = real_client.get(f"/upload/{batch}")
    assert batch_resp.json == resp.json["result"][0]

    # nonexistent batch
    resp = real_client.get("/upload/0")
    assert resp.status_code == 404

    resp = real_client.get("/file?q=nonexistent")
    assert resp.status_code == 200
    assert resp.json == {"result": []}

    resp = real_client.get("/file?q=test.txt")
    assert resp.status_code == 200
    assert len(resp.json["result"]) == 1, resp.json

    resp = real_client.get(f"/file?q={DIGEST[:10]}")
    assert resp.status_code == 200
    assert len(resp.json["result"]) == 1, resp.json

    resp = real_client.get(f"/file/sha512/{DIGEST}")
    assert resp.status_code == 200
    assert resp.json == {
        "algorithm": "sha512",
        "digest": DIGEST,
        "has_instances": True,
        "instances": ["us-east-1"],
        "size": 1,
        "visibility": "public",
    }

    resp = real_client.get(f"/sha512/{DIGEST}")
    assert resp.status_code == 302
    assert resp.headers["location"].startswith(f"https://bucket.s3.amazonaws.com/sha512/{DIGEST}")

    resp = real_client.patch(
        f"/file/sha512/{DIGEST}",
        json=[{"op": "set_visibility", "visibility": "internal"}],
    )
    assert resp.status_code == 401

    flask.g.pop("_login_user", None)
    ext_data = {"scopes": ["project:releng:services/tooltool/api/manage"]}
    manage_header = build_header(client_id, ext_data)

    resp = real_client.patch(
        f"/file/sha512/{DIGEST}",
        json=[{"op": "set_visibility", "visibility": "internal"}],
        headers=[("Authorization", manage_header)],
    )
    assert resp.status_code == 200
    assert resp.json == {
        "algorithm": "sha512",
        "digest": DIGEST,
        "has_instances": True,
        "instances": ["us-east-1"],
        "size": 1,
        "visibility": "internal",
    }

    resp = real_client.get(f"/sha512/{DIGEST}")
    assert resp.status_code == 403

    flask.g.pop("_login_user", None)
    ext_data = {"scopes": ["project:releng:services/tooltool/api/download/internal"]}
    download_header = build_header(client_id, ext_data)

    resp = real_client.get(
        f"/sha512/{DIGEST}",
        headers=[("Authorization", download_header)],
    )
    assert resp.status_code == 302
    assert resp.headers["location"].startswith(f"https://bucket.s3.amazonaws.com/sha512/{DIGEST}")

    resp = real_client.patch(
        f"/file/sha512/{DIGEST}",
        json=[{"op": "delete_instances"}],
        headers=[("Authorization", manage_header)],
    )
    assert resp.status_code == 200
    assert resp.json == {
        "algorithm": "sha512",
        "digest": DIGEST,
        "has_instances": False,
        "instances": [],
        "size": 1,
        "visibility": "internal",
    }

    resp = real_client.get(
        f"/sha512/{DIGEST}",
        headers=[("Authorization", download_header)],
    )
    assert resp.status_code == 404


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def s3(aws_credentials):
    """
    Return a mocked S3 client
    """
    with moto.mock_aws():
        yield boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def bucket(s3):
    s3.create_bucket(Bucket="bucket")
