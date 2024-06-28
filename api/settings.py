# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64
import functools
import os

import tooltool_api.lib.pulse
import tooltool_api.lib.security


def compose(*functions):
    return functools.reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)


def required(variable):
    if variable in os.environ:
        return os.environ[variable]
    raise RuntimeError(f"{variable} environment variable is required")


def as_int(default):
    return compose(int, default)


def as_bool(default):
    return compose(lambda x: str(x).lower() in ["1", "true"], default)


def as_dict(default):
    return compose(lambda x: {i.split(":")[0].strip(): i.split(":")[1].strip() for i in x.split(";")}, default)


def b64decode(default):
    return compose(base64.b64decode, default)


def default(default_value):
    def _default(variable):
        if variable in os.environ:
            return os.environ[variable]
        return default_value

    return _default


# -- LOAD SECRETS -------------------------------------------------------------

DISABLE_PULSE = as_bool(default(False))("DISABLE_PULSE")
CLOUDFRONT_URL = default(None)("CLOUDFRONT_URL")
if CLOUDFRONT_URL:
    CLOUDFRONT_PRIVATE_KEY = required("CLOUDFRONT_PRIVATE_KEY")
else:
    CLOUDFRONT_PRIVATE_KEY = None

if "S3_REGIONS" in os.environ:
    S3_REGIONS = as_dict(default({}))("S3_REGIONS")
else:
    S3_REGIONS = {}

secrets = {
    item: default(item)
    for (item, default) in [
        # environment in which we should run this application
        ("ENV", required),
        # tooltool_api specific secrets, for more details look at src/tooltool_api/api.py
        ("UPLOAD_EXPIRES_IN", as_int(default(60))),
        ("DOWLOAD_EXPIRES_IN", as_int(default(60))),
        ("ALLOW_ANONYMOUS_PUBLIC_DOWNLOAD", as_bool(default(True))),
        ("S3_REGIONS_ACCESS_KEY_ID", required if S3_REGIONS else default(None)),
        ("S3_REGIONS_SECRET_ACCESS_KEY", required if S3_REGIONS else default(None)),
        ("CLOUDFRONT_KEY_ID", required if CLOUDFRONT_URL else default(None)),
        # taskcluster instance url
        ("TASKCLUSTER_ROOT_URL", default("https://firefox-ci-tc.services.mozilla.com")),
        # Database connection string, for more details look at src/tooltool_api/lib/db.py
        ("DATABASE_URL", required),
        # Log errors to sentry, for more details look at src/tooltool_api/lib/log.py
        ("SENTRY_DSN", default(None)),
        # Authentication, for more details look at src/tooltool_api/lib/auth.py
        ("TASKCLUSTER_AUTH", as_bool(default(True))),
        ("SECRET_KEY", b64decode(required)),
        # Cors, for more details look at src/tooltool_api/lib/cors.py
        ("CORS_ORIGINS", default("*")),
        ("CORS_RESOURCES", default("*")),
        # Security, for more details look at src/tooltool_api/lib/security.py
        ("SECURITY", default(tooltool_api.lib.security.DEFAULT_CONFIG)),
        ("SECURITY_CSP_REPORT_URI", default(None)),
        # Pulse, for more details look at src/tooltool_api/lib/pulse.py
        ("PULSE_USER", required if not DISABLE_PULSE else default(None)),
        ("PULSE_PASSWORD", required if not DISABLE_PULSE else default(None)),
        ("PULSE_HOST", default(tooltool_api.lib.pulse.DEFAULT_CONFIG["PULSE_HOST"])),
        ("PULSE_PORT", as_int(default(tooltool_api.lib.pulse.DEFAULT_CONFIG["PULSE_PORT"]))),
        ("PULSE_VIRTUAL_HOST", default(tooltool_api.lib.pulse.DEFAULT_CONFIG["PULSE_VIRTUAL_HOST"])),
        ("PULSE_USE_SSL", as_bool(default(tooltool_api.lib.pulse.DEFAULT_CONFIG["PULSE_USE_SSL"]))),
        ("PULSE_CONNECTION_TIMEOUT", as_int(default(tooltool_api.lib.pulse.DEFAULT_CONFIG["PULSE_CONNECTION_TIMEOUT"]))),
    ]
}

locals().update(secrets)

with open(os.path.join(os.path.dirname(__file__), "version.txt")) as f:
    VERSION = f.read().strip()

if CLOUDFRONT_PRIVATE_KEY:
    with open(CLOUDFRONT_PRIVATE_KEY, "rb") as key:
        CLOUDFRONT_PRIVATE_KEY = key.read().strip()

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = secrets["DATABASE_URL"]

if ENV == "localdev":  # type: ignore[name-defined]  # noqa: F821
    SQLALCHEMY_ECHO = True
