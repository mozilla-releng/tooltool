ARG BASE_IMAGE
FROM $BASE_IMAGE
LABEL maintainer="Mozilla Release Engineering <release+docker@mozilla.com>"

VOLUME /builds/worker/checkouts
VOLUME /builds/worker/.cache

# Add worker user
RUN mkdir -p /builds && \
    adduser --home /builds/worker --shell /bin/sh --disabled-password --gecos '' worker && \
    mkdir /builds/worker/artifacts && \
    chown -R worker:worker /builds/worker

# %include-run-task

ENV HOME=/builds/worker \
    PATH=/builds/worker/.local/bin:$PATH

RUN apt-get update && apt-get install -y jq && pip install tox tox-uv
ARG SETUP_COMMAND
RUN eval $SETUP_COMMAND

# Set a default command useful for debugging
CMD ["/bin/sh"]
