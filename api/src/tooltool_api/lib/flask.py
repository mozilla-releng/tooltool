# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import importlib
import os

import flask

import tooltool_api.lib.dockerflow
import tooltool_api.lib.log

EXTENSIONS = ["log", "security", "cors", "api", "auth", "pulse", "db"]

logger = tooltool_api.lib.log.get_logger(__name__)


def create_app(project_name, extensions=[], config=None, enable_dockerflow=True, **kw):
    """
    Create a new Flask backend application
    project_name is the Python application name, used as Flask import_name
    project_name is a "nice" name, used to identify the application
    """
    logger.debug("Initializing", app=project_name)

    app = flask.Flask(import_name=project_name, **kw)
    app.name = project_name
    app.__extensions = extensions

    if not app.config.get("APP_TESTING") and os.environ.get("APP_SETTINGS"):
        logger.info("Loading custom configuration from APP_SETTINGS", APP_SETTINGS=os.environ.get("APP_SETTINGS"))
        app.config.from_envvar("APP_SETTINGS")

    if config:
        logger.info("Loading custom configuration")
        app.config.update(**config)

    for extension_name in EXTENSIONS:
        if app.config.get("APP_TESTING") and extension_name in ["security", "cors"]:
            continue

        if extension_name not in extensions:
            continue

        logger.debug("Initializing extension", extension=extension_name, app=app.name)

        extension_init_app = None
        try:
            extension_init_app = getattr(importlib.import_module("tooltool_api.lib." + extension_name), "init_app")
        except Exception as e:
            logger.exception(e)
            pass

        if extension_init_app is None:
            raise Exception(f"Could not import tooltool_api.lib extension: {extension_name}")

        extension = extension_init_app(app)
        if extension and extension_name is not None:
            setattr(app, extension_name, extension)

        logger.debug("Extension initialized", extension=extension_name, app=app.name)

    app.add_url_rule("/", "root", lambda: flask.redirect("/static/ui/index.html"))

    if enable_dockerflow:
        app.add_url_rule("/__heartbeat__", view_func=tooltool_api.lib.dockerflow.heartbeat_response)
        app.add_url_rule("/__lbheartbeat__", view_func=tooltool_api.lib.dockerflow.lbheartbeat_response)
        app.add_url_rule("/__version__", view_func=tooltool_api.lib.dockerflow.get_version)

    logger.debug("Initialized", app=app.name)
    return app
