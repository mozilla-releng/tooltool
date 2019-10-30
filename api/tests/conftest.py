# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64
import datetime
import json
import os
import re

import flask
import flask_login
import logbook
import pytest
import responses


@pytest.fixture(scope='session')
def app():
    '''Configure a mock application to run queries against

    Build an app with an authenticated dummy api
    '''
    import backend_common

    # Use unique auth instance
    config = get_app_config({
        'OIDC_CLIENT_SECRETS': os.path.join(os.path.dirname(__file__), 'client_secrets.json'),
        'OIDC_RESOURCE_SERVER_ONLY': True,
        'APP_TEMPLATES_FOLDER': '',
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'AUTH_CLIENT_ID': 'dummy_id',
        'AUTH_CLIENT_SECRET': 'dummy_secret',
        'AUTH_DOMAIN': 'auth.localhost',
        'AUTH_REDIRECT_URI': 'http://localhost/login',
    })

    app = backend_common.create_app(
        app_name='test',
        project_name='Test',
        extensions=backend_common.EXTENSIONS,
        config=config,
    )

    @app.route('/')
    def index():
        return app.response_class('OK')

    @app.route('/test-auth-login')
    @backend_common.auth.auth.require_login
    def logged_in():
        data = {
            'auth': True,
            'user': flask_login.current_user.get_id(),
            # permissions is a set, not serializable
            'scopes': list(flask_login.current_user.permissions),
        }
        return flask.jsonify(data)

    @app.route('/test-auth-scopes')
    @backend_common.auth.auth.require_permissions([
        ['project/test/A', 'project/test/B'],
        ['project/test-admin/*'],
    ])
    def scopes():
        return app.response_class('Your scopes are ok.')

    # Add fake swagger url, used by redirect
    app.api.swagger_url = '/'

    with app.app_context():
        configure_app(app)
        yield app


def get_app_config(extra_config):
    config = {
        'TESTING': True,
        'SECRET_KEY': os.urandom(24)
    }
    config.update(extra_config)
    return config


requests_mock = responses.RequestsMock(assert_all_requests_are_fired=False)


def parse_header(header):
    '''Parse a fake Hawk header

       Extract client id and ext data
    '''
    if not header.startswith('Hawk '):
        raise Exception('Missing Hawk prefix')

    # Load header parts
    parts = re.findall(r'(\w+)="([\w=\.\@\-_/]+)"', header)
    if parts is None:
        raise Exception('Invalid header structure')
    parts = dict(parts)
    for k in ('id', 'mac', 'ts', 'nonce'):
        if k not in parts:
            raise Exception(f'Missing header part {k}')

    # TODO: check mac

    # Load ext data
    try:
        ext_data = json.loads(base64.b64decode(parts['ext']).decode('utf-8'))
    except Exception:
        ext_data = {}

    return parts['id'], ext_data


def mock_auth_taskcluster(request):
    '''Mock the hawk header validation from Taskcluster.
    '''
    payload = json.loads(request.body)
    try:
        # Parse fake hawk header
        if 'authorization' not in payload:
            raise Exception('Missing authorization')
        client_id, ext_data = parse_header(payload['authorization'])

        # Build success response
        expires = datetime.datetime.now() + datetime.timedelta(days=1)
        body = {
            'status': 'auth-success',
            'scopes': ext_data.get('scopes', []),
            'scheme': 'hawk',
            'clientId': client_id,
            'expires': expires.strftime('%Y-%m-%dT%H:%M:%S'),
        }
        http_code = 200

    except Exception as e:
        # Build failure response
        body = {
            'status': 'auth-failure',
            'message': str(e),
        }
        http_code = 401

    # Output response
    headers = {
        'Content-Type': 'application/json'
    }
    return (http_code, headers, json.dumps(body))


def configure_app(app):
    '''Configure flask application and ensure all mocks are in place
    '''

    if hasattr(app, 'db'):
        app.db.drop_all()
        app.db.create_all()


@pytest.fixture(autouse=True)
def client(app):
    '''A Flask test client for uplift/backend with mockups enabled.
    '''
    with app.test_client() as client:
        with requests_mock:

            if hasattr(app, 'auth'):
                requests_mock.add_callback(
                    responses.POST,
                    'http://zzz/api/auth/v1/authenticate-hawk',
                    callback=mock_auth_taskcluster,
                    content_type='application/json',
                )

            yield client


@pytest.fixture(scope='module')
def logger():
    '''
    Build a logger
    '''

    import cli_common.log

    cli_common.log.init_logger('cli_common', level=logbook.DEBUG)
    return cli_common.log.get_logger(__name__)
