FROM ghcr.io/astral-sh/uv:0.7.9 as uv
FROM python:3.13

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
