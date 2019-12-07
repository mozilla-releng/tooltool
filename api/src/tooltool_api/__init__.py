# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import typing

import flask
import werkzeug.exceptions

import tooltool_api.aws
import tooltool_api.cli
import tooltool_api.config
import tooltool_api.lib
import tooltool_api.lib.api
import tooltool_api.models  # noqa
import tooltool_api.view


def custom_handle_default_exceptions(e: Exception) -> typing.Tuple[int, str]:
    """Conform structure of errors as before, to make it work with client (tooltool.py).
    """
    error = tooltool_api.lib.api.handle_default_exceptions_raw(e)
    error["name"] = error["title"]
    error["description"] = error["detail"]
    import flask  # for some reason flask needs to be imported here

    return flask.jsonify(dict(error=error)), error["status"]


def create_app(config: dict = None) -> flask.Flask:
    app = tooltool_api.lib.flask.create_app(
        project_name=tooltool_api.config.PROJECT_NAME,
        config=config,
        extensions=["log", "security", "cors", "api", "auth", "db", "pulse"],
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )
    app.api.register(os.path.join(os.path.dirname(__file__), "api.yml"))
    app.aws = tooltool_api.aws.AWS(app.config["S3_REGIONS_ACCESS_KEY_ID"], app.config["S3_REGIONS_SECRET_ACCESS_KEY"])

    for code, exception in werkzeug.exceptions.default_exceptions.items():
        app.register_error_handler(exception, custom_handle_default_exceptions)

    app.cli.add_command(tooltool_api.cli.cmd_worker, "worker")
    app.cli.add_command(tooltool_api.cli.cmd_replicate, "replicate")
    app.cli.add_command(tooltool_api.cli.cmd_check_pending_uploads, "check-pending-uploads")

    app.add_url_rule("/tooltool.py", view_func=tooltool_api.view.download_client)

    return app
