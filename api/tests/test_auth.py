# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64
import collections
import hashlib
import json
import random
import time

import pytest


def build_header(client_id, ext_data=None):
    '''Build a fake Hawk header to share client id & scopes.
    '''

    out = collections.OrderedDict({
        'id': client_id,
        'ts': int(time.time()),
        'nonce': random.randint(0, 100000),
    })
    if ext_data is not None:
        json_data = json.dumps(ext_data, sort_keys=True).encode('utf-8')
        out['ext'] = base64.b64encode(json_data).decode('utf-8')

    mac_contents = '\n'.join(map(str, out.values()))
    out['mac'] = hashlib.sha1(mac_contents.encode('utf-8')).hexdigest()

    parts = map(lambda x: '{}="{}"'.format(*x), out.items())
    return 'Hawk {}'.format(', '.join(parts))


def test_anonymous():
    '''
    Test AnonymousUser instances
    '''
    import tooltool_api.lib.auth

    user = tooltool_api.lib.auth.AnonymousUser()

    # Test base
    assert user.get_id() == 'anonymous:'
    assert user.get_permissions() == set()
    assert user.permissions == set()
    assert not user.is_active
    assert user.is_anonymous


def test_taskcluster_user():
    '''
    Test TasklusterUser instances
    '''

    import tooltool_api.lib.auth

    credentials = {
        'clientId': 'test/user@mozilla.com',
        'scopes': ['project:test:*', ]
    }
    user = tooltool_api.lib.auth.TaskclusterUser(credentials)

    # Test base
    assert user.get_id() == credentials['clientId']
    assert user.get_permissions() == credentials['scopes']
    assert user.permissions == credentials['scopes']
    assert user.is_active
    assert not user.is_anonymous

    # Test invalid input
    with pytest.raises(Exception):
        user = tooltool_api.lib.auth.TaskclusterUser({})
    with pytest.raises(Exception):
        user = tooltool_api.lib.auth.TaskclusterUser({'clientId': '', 'scopes': None})


def test_auth(client):
    '''
    Test the Taskcluster authentication
    '''

    # Test non authenticated endpoint
    resp = client.get('/')
    assert resp.status_code in (200, 302)

    # Test authenticated endpoint without header
    resp = client.get('/test-auth-login')
    assert resp.status_code == 401

    # Test authenticated endpoint with header
    ext_data = {
        'scopes': ['project/test/*', ],
    }
    client_id = 'test/user@mozilla.com'
    header = build_header(client_id, ext_data)
    resp = client.get('/test-auth-login', headers=[('Authorization', header)])
    assert resp.status_code == 200
    data = json.loads(resp.data.decode('utf-8'))
    assert data['auth']
    assert data['user'] == client_id
    assert data['scopes'] == ext_data['scopes']


def test_scopes_invalid(client):
    '''
    Test the Taskcluster required scopes
    '''

    client_id = 'test/user@mozilla.com'

    # Missing a scope to validate test
    ext_data = {
        'scopes': ['project/test/A', 'project/test/C', ],
    }
    header = build_header(client_id, ext_data)
    resp = client.get('/test-auth-scopes', headers=[('Authorization', header)])
    assert resp.status_code == 401


def test_scopes_user(client):
    '''
    Test the Taskcluster required scopes
    '''

    client_id = 'test/user@mozilla.com'
    # Validate with user scopes
    ext_data = {
        'scopes': ['project/test/A', 'project/test/B', ],
    }
    header = build_header(client_id, ext_data)
    resp = client.get('/test-auth-scopes',
                      headers=[('Authorization', header)])
    assert resp.status_code == 200
    assert resp.data == b'Your scopes are ok.'


def test_scopes_admin(client):
    '''
    Test the Taskcluster required scopes
    '''

    client_id = 'test/user@mozilla.com'

    # Validate with admin scopes
    ext_data = {
        'scopes': ['project/another/*', 'project/test-admin/*']
    }
    header = build_header(client_id, ext_data)
    resp = client.get('/test-auth-scopes', headers=[('Authorization', header)])
    assert resp.status_code == 200
    assert resp.data == b'Your scopes are ok.'
