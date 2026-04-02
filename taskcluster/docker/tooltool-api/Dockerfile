FROM ghcr.io/astral-sh/uv:0.11.3@sha256:90bbb3c16635e9627f49eec6539f956d70746c409209041800a0280b93152823 as uv
FROM python:3.14@sha256:ffebef43892dd36262fa2b042eddd3320d5510a21f8440dce0a650a3c124b51d

COPY --from=uv /uv /bin

RUN groupadd --gid 10001 app && \
    useradd -g app --uid 10001 --shell /usr/sbin/nologin --create-home --home-dir /app app

RUN apt-get update \
 && ln -s /app/docker.d/healthcheck /bin/healthcheck

ENV APP_SETTINGS /app/settings.py
ENV FLASK_APP tooltool_api.flask:app
ENV WEB_CONCURRENCY=3

ENV PATH="/app/.venv/bin:${PATH}"

# This build argument lets us share the Dockerfile between docker compose and image_builder
ARG SRC=topsrcdir

# %include api
COPY ${SRC}/api/ /app

RUN chown -R app:app /app

USER app
WORKDIR /app

ARG FRONTEND_CONFIG
RUN cp /app/src/tooltool_api/static/${FRONTEND_CONFIG} /app/src/tooltool_api/static/config.mjs

RUN /bin/uv sync --no-dev --locked

CMD ["/app/docker.d/run.sh"]
