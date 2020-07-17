# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# %ARG PYTHON_VERSION
FROM          python:$PYTHON_VERSION
MAINTAINER    Tom Prince <tom.prince@mozilla.com>

# Add worker user
RUN mkdir /builds && \
    useradd -d /builds/worker -s /bin/bash -m worker && \
    chown worker:worker /builds/worker && \
    mkdir /builds/worker/artifacts && \
    chown worker:worker /builds/worker/artifacts

# %include-run-task

ENV SHELL=/bin/bash \
    HOME=/builds/worker \
    PATH=/builds/worker/.local/bin:$PATH

VOLUME /builds/worker/checkouts
VOLUME /builds/worker/.cache


RUN apt-get update && apt-get install -y -f \
    zip \
    xz-utils \
    build-essential \
    libssl-dev \
    libffi-dev

# Set a default command useful for debugging
CMD ["/bin/bash", "--login"]
