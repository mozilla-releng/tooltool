# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM debian:13-slim@sha256:f6b08b09a05725f9431502d3b5714f5c4576e82c1a84fa1debe0c24a7e0c3ec4
LABEL maintainer="Release Engineering <release@mozilla.com>"

# %include-run-task

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq \
    && apt-get dist-upgrade -y \
    && apt-get install -y jq zstd python3-minimal curl skopeo umoci \
    && apt-get clean

COPY push_image.sh /usr/local/bin/
COPY policy.json /etc/containers/policy.json
RUN chmod a+x /usr/local/bin/push_image.sh

# Add worker user
RUN mkdir -p /builds && \
    groupadd -g 1000 -o worker && \
    useradd -d /builds/worker -s /bin/bash -m worker -g 1000 -o -u 1000 && \
    mkdir /builds/worker/artifacts && \
    chown worker:worker /builds/worker/artifacts

USER worker
ENV SHELL=/bin/bash \
    HOME=/builds/worker \
    USER=worker

WORKDIR /builds/worker
# Set a default command useful for debugging
CMD ["/bin/bash", "--login"]
