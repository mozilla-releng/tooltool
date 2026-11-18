FROM ghcr.io/astral-sh/uv:0.12.9@sha256:8b940d3a9d65bed080436972241af2e21c84b5e8c9193f7014ed71479ee795ff as uv
FROM python:3.14@sha256:22caa054c0d309b1eee6f448326a8821a674a75b98653247fe706db90491fc87

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

# Include only what's needed, rather than all of api/, to avoid picking up
# local state such as api/.venv (taskgraph has no exclude mechanism).
# %include api/pyproject.toml
COPY ${SRC}/api/pyproject.toml /app/pyproject.toml
# %include api/uv.lock
COPY ${SRC}/api/uv.lock /app/uv.lock
# %include api/settings.py
COPY ${SRC}/api/settings.py /app/settings.py
# %include api/docker.d
COPY ${SRC}/api/docker.d/ /app/docker.d/
# %include api/src
COPY ${SRC}/api/src/ /app/src/

RUN chown -R app:app /app

USER app
WORKDIR /app

ARG FRONTEND_CONFIG
RUN cp /app/src/tooltool_api/static/${FRONTEND_CONFIG} /app/src/tooltool_api/static/config.mjs

RUN /bin/uv sync --no-dev --locked

CMD ["/app/docker.d/run.sh"]
