# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import flask

TOOLTOOL_PY_URL = 'https://raw.githubusercontent.com/mozilla-releng/tooltool/master/client/tooltool.py'


def download_client():
    return flask.redirect(TOOLTOOL_PY_URL)
