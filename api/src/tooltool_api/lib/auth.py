# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import functools
import json

import flask
import flask_login
import flask_oidc
import taskcluster
import taskcluster.utils

import tooltool_api.lib.db
import tooltool_api.lib.dockerflow
import tooltool_api.lib.log

logger = tooltool_api.lib.log.get_logger(__name__)

UNAUTHORIZED_JSON = {
    'status': 401,
    'title': '401 Unauthorized: Invalid user permissions',
    'detail': 'Invalid user permissions',
    'instance': 'about:blank',
    'type': 'about:blank',
}


class BaseUser(object):

    anonymous = False
    type = None

    def __eq__(self, other):
        return isinstance(other, BaseUser) and self.get_id() == other.get_id()

    @property
    def is_authenticated(self):
        return not self.anonymous

    @property
    def is_active(self):
        return not self.anonymous

    @property
    def is_anonymous(self):
        return self.anonymous

    @property
    def permissions(self):
        return self.get_permissions()

    def get_permissions(self):
        return set()

    def get_id(self):
        raise NotImplementedError

    def has_permissions(self, permissions):

        if not isinstance(permissions, (tuple, list)):
            permissions = [permissions]

        user_permissions = self.get_permissions()

        return all([
            permission in list(user_permissions)
            for permission in permissions
        ])

    def __str__(self):
        return self.get_id()


class AnonymousUser(BaseUser):

    anonymous = True
    type = 'anonymous'

    def get_id(self):
        return 'anonymous:'


class TaskclusterUser(BaseUser):

    type = 'taskcluster'

    def __init__(self, credentials):
        if not isinstance(credentials, dict):
            raise Exception('credentials should be a dict')

        if 'clientId' not in credentials:
            raise Exception(f'credentials should contain clientId, {credentials}')

        if not isinstance(credentials['clientId'], str):
            raise Exception('credentials["clientId"] should be a string')

        if 'scopes' not in credentials:
            raise Exception('credentials should contain scopes')

        if not isinstance(credentials['scopes'], list):
            raise Exception('credentials["scopes"] should be a list')

        self.credentials = credentials

        logger.info(f'Init user {self.get_id()}')

    def get_id(self):
        return self.credentials['clientId']

    def get_permissions(self):
        return self.credentials['scopes']

    def has_permissions(self, permissions):
        '''
        Check user has some required permissions
        Using Taskcluster comparison algorithm
        '''
        if not isinstance(permissions, (tuple, list)):
            permissions = [permissions]

        if not isinstance(permissions[0], (tuple, list)):
            permissions = [permissions]

        return taskcluster.utils.scopeMatch(self.get_permissions(), permissions)


class Auth(object):

    def __init__(self, anonymous_user):
        self.login_manager = flask_login.LoginManager()
        self.login_manager.anonymous_user = anonymous_user
        self.app = None

    def init_app(self, app):
        self.app = app
        self.login_manager.init_app(app)

    def _require_login(self):
        with flask.current_app.app_context():
            try:
                return flask_login.current_user.is_authenticated
            except Exception as e:
                logger.error(f'Invalid authentication: {e}')
                return False

    def require_login(self, method):
        '''Decorator to check if user is authenticated
        '''
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            if self._require_login():
                return method(*args, **kwargs)
            return 'Unauthorized', 401
        return wrapper

    def _require_permissions(self, permissions):
        if not self._require_login():
            return False

        with flask.current_app.app_context():
            if not flask_login.current_user.has_permissions(permissions):
                user = flask_login.current_user.get_id()
                user_permissions = flask_login.current_user.get_permissions()
                diff = ' OR '.join([
                    ', '.join(set(p).difference(user_permissions))
                    for p in permissions
                ])
                logger.error(f'User {user} misses some permissions: {diff}')
                return False

        return True

    def require_permissions(self, permissions):
        '''Decorator to check if user has required permissions or set of
           permissions
        '''

        def decorator(method):
            @functools.wraps(method)
            def wrapper(*args, **kwargs):
                logger.info('Checking permissions', permissions=permissions)
                if self._require_permissions(permissions):
                    # Validated permissions, running method
                    logger.info('Validated permissions, processing api request')
                    return method(*args, **kwargs)
                else:
                    # Abort with a 401 status code
                    return flask.jsonify(UNAUTHORIZED_JSON), 401
            return wrapper
        return decorator


auth0 = flask_oidc.OpenIDConnect()
auth = Auth(
    anonymous_user=AnonymousUser,
)


def jti2id(jti):
    if jti[0] != 't':
        raise TypeError('jti not in the format `t$token_id`')
    return int(jti[1:])


NO_AUTH = object()
PERMISSIONS = {
    'project:releng:services/tooltool/download/internal': 'Download INTERNAL files from tooltool',
    'project:releng:services/tooltool/download/public': 'Download PUBLIC files from tooltool',
    'project:releng:services/tooltool/manage': 'Manage tooltool files, including deleting and changing visibility levels',
    'project:releng:services/tooltool/upload/internal': 'Upload INTERNAL files to tooltool',
    'project:releng:services/tooltool/upload/public': 'Upload PUBLIC files to tooltool'
}


def initial_data():
    user = dict()
    user['type'] = flask_login.current_user.type

    user['permissions'] = []
    for permission, permission_doc in PERMISSIONS.items():
        if flask_login.current_user.has_permissions(permission):
            user['permissions'].append(dict(
                name=permission,
                doc=permission_doc,
            ))

    if getattr(flask_login.current_user, 'authenticated_email', NO_AUTH) != NO_AUTH:
        user['authenticated_email'] = flask_login.current_user.authenticated_email

    return dict(
        user=user,
        perms=PERMISSIONS,
    )


def parse_header_taskcluster(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        auth_header = request.headers.get('Authentication')
    if not auth_header:
        return NO_AUTH
    if not auth_header.startswith('Hawk'):
        return NO_AUTH

    # Get Endpoint configuration
    if ':' in request.host:
        host, port = request.host.split(':')
    else:
        host = request.host
        port = request.environ.get('HTTP_X_FORWARDED_PORT')
        if port is None:
            port = request.scheme == 'https' and 443 or 80
    method = request.method.lower()

    # Build taskcluster payload
    payload = {
        'resource': request.path,
        'method': method,
        'host': host,
        'port': int(port),
        'authorization': auth_header,
    }

    # Auth with taskcluster
    auth = taskcluster.Auth(dict(rootUrl=flask.current_app.config['TASKCLUSTER_ROOT_URL']))
    try:
        resp = auth.authenticateHawk(payload)
        if not resp.get('status') == 'auth-success':
            raise Exception('Taskcluster rejected the authentication')
    except Exception as e:
        logger.error(f'TC auth error: {e}')
        logger.error(f'TC auth details: {payload}')
        return NO_AUTH

    return TaskclusterUser(resp)


@auth.login_manager.request_loader
def parse_header(request):
    '''Parse header and try to authenticate
    '''
    if flask.current_app.config.get('TASKCLUSTER_AUTH', False) is True:
        user = parse_header_taskcluster(request)
        if user != NO_AUTH:
            return user


def get_permissions():
    response = dict(
        description='Permissions of a logged in user',
        user_id=None,
        permissions=[],
    )
    user = flask_login.current_user

    if user.is_authenticated:
        response['user_id'] = user.get_id()
        response['permissions'] = user.get_permissions()

    return flask.Response(
        status=200,
        response=json.dumps(response),
        headers={
            'Content-Type': 'application/json',
            'Cache-Control': 'public, max-age=60',
        },
    )


def init_app(app):
    if app.config.get('SECRET_KEY') is None:
        raise Exception('When using `auth` extention you need to specify SECRET_KEY.')

    auth.init_app(app)

    app.add_url_rule('/__permissions__', view_func=get_permissions)

    return auth


def app_heartbeat():
    config = flask.current_app.config
    if config.get('TASKCLUSTER_AUTH') is True:
        auth = taskcluster.Auth(dict(rootUrl=flask.current_app.config['TASKCLUSTER_ROOT_URL']))
        try:
            ping = auth.ping()
            assert ping['alive'] is True
        except Exception as e:
            logger.exception(e)
            raise tooltool_api.lib.dockerflow.HeartbeatException('Cannot connect to the taskcluster auth service.')
