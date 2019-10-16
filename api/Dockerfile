FROM python:3.7

RUN groupadd --gid 10001 app && \
    useradd -g app --uid 10001 --shell /usr/sbin/nologin --create-home --home-dir /app app

RUN apt-get update \
 && ln -s /app/docker.d/healthcheck /bin/healthcheck

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
