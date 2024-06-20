FROM python:3.11

RUN groupadd --gid 10001 app && \
    useradd -g app --uid 10001 --shell /usr/sbin/nologin --create-home --home-dir /app app

RUN apt-get update \
 && ln -s /app/docker.d/healthcheck /bin/healthcheck

ENV APP_SETTINGS /app/settings.py
ENV FLASK_APP tooltool_api.flask:app
ENV WEB_CONCURRENCY=3

ENV PATH="/appenv/bin:${PATH}"

COPY . /app

RUN mkdir /appenv \
 && chown -R app:app /app /appenv

USER app
WORKDIR /app

RUN python -m venv /appenv \
 && /appenv/bin/pip install --upgrade pip \
 && /appenv/bin/pip install -r requirements/base.txt \
 && /appenv/bin/pip install -e .

CMD ["/app/docker.d/run.sh"]
