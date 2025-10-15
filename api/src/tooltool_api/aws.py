# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import boto3
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

import tooltool_api.lib.log

logger = tooltool_api.lib.log.get_logger(__name__)


class AWS(object):
    def __init__(self, access_key_id, secret_access_key):
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self._sessions = {}

    def connect_to(self, service_name, region_name):
        key = region_name
        if key in self._sessions:
            session = self._sessions[key]
        else:
            session = boto3.Session(aws_access_key_id=self.access_key_id, aws_secret_access_key=self.secret_access_key, region_name=region_name)
            self._sessions[key] = session
        return session.resource(service_name)

    def generate_presigned_cloudfront_url(self, url, expire_time, keypair_id, private_key_string):
        # From https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudfront.html#generate-a-signed-url-for-amazon-cloudfront
        def rsa_signer(message):
            private_key = serialization.load_pem_private_key(private_key_string, password=None, backend=default_backend())
            return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())

        cloudfront_signer = CloudFrontSigner(keypair_id, rsa_signer)

        # Create a signed url that will be valid until the specfic expiry date
        # provided using a canned policy.
        return cloudfront_signer.generate_presigned_url(url, date_less_than=expire_time)
