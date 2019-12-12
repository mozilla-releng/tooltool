# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import importlib

import boto
import boto.cloudfront.distribution
import boto.s3
import boto.sqs

import tooltool_api.lib.log

logger = tooltool_api.lib.log.get_logger(__name__)


class AWS(object):
    def __init__(self, access_key_id, secret_access_key):
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self._connections = {}
        self._queues = {}
        self._listeners = []

    def connect_to(self, service_name, region_name):
        key = service_name, region_name
        if key in self._connections:
            return self._connections[key]

        # handle special cases
        try:
            fn = getattr(self, "connect_to_" + service_name)
        except AttributeError:
            fn = self.connect_to_default
        conn = fn(service_name, region_name)
        self._connections[key] = conn
        return conn

    def connect_to_default(self, service_name, region_name):
        # for the service, import 'boto.$service'
        service = importlib.import_module("boto." + service_name)

        for region in service.regions():
            if region.name == region_name:
                break
        else:
            raise RuntimeError("invalid region %r" % (region_name,))

        connect_fn = getattr(boto, "connect_" + service_name)
        return connect_fn(region=region, aws_access_key_id=self.access_key_id, aws_secret_access_key=self.secret_access_key)

    def connect_to_s3(self, service_name, region_name):
        # special case for S3, which boto does differently than
        # the other services
        return boto.s3.connect_to_region(region_name=region_name, aws_access_key_id=self.access_key_id, aws_secret_access_key=self.secret_access_key)

    def connect_to_cloudfront(self, service_name, region_name):
        # special case for cloudfront, which boto does differently than
        # the other services
        return boto.cloudfront.Distribution(aws_access_key_id=self.access_key_id, aws_secret_access_key=self.secret_access_key,)
