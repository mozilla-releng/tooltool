# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pathlib

from connexion.apis.flask_api import FlaskApi

import tooltool_api.lib.log

logger = tooltool_api.lib.log.get_logger(__name__)


class Api:
    """TODO: add description
    TODO: annotate class
    """

    def __init__(self, app):
        """
        TODO: add description
        TODO: annotate function
        """
        self.__app = app

    def register(
        self,
        specification,
        base_path=None,
        arguments=None,
        validate_responses=True,
        strict_validation=True,
        resolver=None,
        auth_all_paths=False,
        debug=False,
        resolver_error_handler=None,
        validator_map=None,
        pythonic_params=False,
        pass_context_arg_name=None,
        options=dict(swagger_url="apidocs"),
    ):
        """Adds an API to the application based on a swagger file"""

        app = self.__app
        logger.debug(f"Adding API: {specification}")

        self.__api = api = FlaskApi(
            specification=pathlib.Path(specification),
            base_path=base_path,
            arguments=arguments,
            validate_responses=validate_responses,
            strict_validation=strict_validation,
            resolver=resolver,
            auth_all_paths=auth_all_paths,
            debug=app.debug,
            resolver_error_handler=resolver_error_handler,
            validator_map=validator_map,
            pythonic_params=pythonic_params,
            pass_context_arg_name=pass_context_arg_name,
            options=options,
        )
        self.swagger_url = api.options.openapi_console_ui_path
        app.register_blueprint(api.blueprint)

        return api


def init_app(app):
    return Api(app)


def app_heartbeat():
    pass
