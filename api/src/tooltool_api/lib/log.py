# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import logbook
import logbook.compat
import structlog
import structlog.exceptions

ENVS = [
    "test",  # for running tests
    "localdev",  # for local development
    "dev",  # dev environment on GCP
    "staging",  # staging environment on GCP
    "production",  # production environment on GCP
]


class UnstructuredRenderer(structlog.processors.KeyValueRenderer):
    def __call__(self, logger, method_name, event_dict):
        event = None
        if "event" in event_dict:
            event = event_dict.pop("event")
        if event_dict or event is None:
            # if there are other keys, use the parent class to render them
            # and append to the event
            rendered = super(UnstructuredRenderer, self).__call__(logger, method_name, event_dict)
            return "%s (%s)" % (event, rendered)
        else:
            return event


def setup_sentry(project_name, env, SENTRY_DSN, flask_app=None):
    """
    Setup sentry account using taskcluster secrets
    """

    import sentry_sdk

    config = dict(dsn=SENTRY_DSN, environment=env)

    if flask_app:
        version = flask_app.config.get("VERSION")
        if version:
            config["release"] = version

    sentry_sdk.init(**config)


def init_logger(project_name, env, level=logbook.INFO, handler=None, SENTRY_DSN=None, flask_app=None, timestamp=False):

    if env and env not in ENVS:
        raise Exception("Initializing logging with env `{}`. It should be one of: {}".format(env, ", ".join(ENVS)))

    # By default output logs on stderr
    if handler is None:
        fmt = "{record.channel}: {record.message}"
        handler = logbook.StderrHandler(level=level, format_string=fmt)

    handler.push_application()

    # Log to sentry
    if env and SENTRY_DSN:
        setup_sentry(project_name, env, SENTRY_DSN, flask_app)

    def logbook_factory(*args, **kwargs):
        # Logger given to structlog
        logbook.compat.redirect_logging()
        return logbook.Logger(level=level, *args, **kwargs)

    # Setup structlog over logbook
    processors = [structlog.stdlib.PositionalArgumentsFormatter(), structlog.processors.StackInfoRenderer(), structlog.processors.format_exc_info]
    if timestamp is True:
        processors.append(structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"))

    processors.append(UnstructuredRenderer())

    structlog.configure(
        context_class=structlog.threadlocal.wrap_dict(dict),
        processors=processors,
        logger_factory=logbook_factory,
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(*args, **kwargs):
    return structlog.get_logger(*args, **kwargs)


def init_app(app):
    """
    Init logger from a Flask Application
    """
    level = logbook.INFO
    if app.debug:
        level = logbook.DEBUG

    init_logger(app.name, env=os.environ.get("ENV"), level=level, SENTRY_DSN=app.config.get("SENTRY_DSN"), flask_app=app)


def app_heartbeat():
    pass
