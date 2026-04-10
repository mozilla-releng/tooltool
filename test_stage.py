#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Test script for the tooltool staging API.

Creates a sample manifest, uploads a file, then deletes it.

Credentials are read from TASKCLUSTER_CLIENT_ID and TASKCLUSTER_ACCESS_TOKEN
environment variables, or from a JSON file passed via --auth-file.

Usage:
    uv run test_stage.py [--auth-file path/to/creds.json] [--url https://...]
"""

import argparse
import importlib.util
import os
import sys
import tempfile

BASE_URL = "https://stage.tooltool.mozilla-releng.net/"

# Load tooltool.py as a module from the client directory
_tooltool_path = os.path.join(os.path.dirname(__file__), "client", "tooltool.py")
_spec = importlib.util.spec_from_file_location("tooltool", _tooltool_path)
tooltool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tooltool)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--auth-file", help="JSON file with clientId and accessToken")
    parser.add_argument("--url", default=BASE_URL, help=f"Base URL (default: {BASE_URL})")
    args = parser.parse_args()

    orig_dir = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            _run(args, tmpdir)
        finally:
            os.chdir(orig_dir)


def _run(args, tmpdir):
    # --- Step 1: create a test file and manifest ---
    manifest_file = os.path.join(tmpdir, "manifest.tt")

    with open("test_stage.txt", "w") as f:
        f.write("tooltool stage test file\n")

    tooltool.add_files(manifest_file, "sha512", ["test_stage.txt"], version=None, visibility="public", unpack=False)

    manifest = tooltool.open_manifest(manifest_file)
    digest = manifest.file_records[0].digest
    print(f"Manifest created, digest: {digest[:16]}...")

    # --- Step 2: upload ---
    print(f"\n==> upload")
    ok = tooltool.upload(
        manifest=manifest_file,
        message="tooltool stage test upload",
        base_urls=[args.url],
        auth_file=args.auth_file,
        region=None,
    )
    if not ok:
        print("Upload failed.", file=sys.stderr)
        sys.exit(1)
    print("Upload complete.")

    # --- Step 3: delete instances ---
    print(f"\n==> delete_instances")
    ok = tooltool.delete_instances(
        base_urls=[args.url],
        digest=digest,
        auth_file=args.auth_file,
    )
    if not ok:
        print("Delete failed.", file=sys.stderr)
        sys.exit(1)
    print("Deleted. Done.")


if __name__ == "__main__":
    main()
