#!/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -e -x

test $NAME
test $VERSION
test $DOCKER_REPO
test $DOCKER_TAG
test $MOZ_FETCHES_DIR
test $SECRET_URL
test $TASKCLUSTER_ROOT_URL
test $TASK_ID
test $VCS_HEAD_REPOSITORY
test $VCS_HEAD_REV

echo "=== Generating dockercfg ==="
install -m 600 /dev/null $HOME/.dockercfg
# Note: If there's a scoping error, this will not fail, causing the skopeo copy command to fail
curl $SECRET_URL | jq '.secret.docker.dockercfg' > $HOME/.dockercfg

export REGISTRY_AUTH_FILE=$HOME/.dockercfg

cd $MOZ_FETCHES_DIR
unzstd image.tar.zst

echo "=== Inserting version.json into image ==="
# Create an OCI copy of image in order umoci can patch it
skopeo copy docker-archive:image.tar oci:${NAME}:final

cat > version.json <<EOF
{
    "commit": "${VCS_HEAD_REV}",
    "version": "${VERSION}",
    "source": "${VCS_HEAD_REPOSITORY}",
    "build": "${TASKCLUSTER_ROOT_URL}/tasks/${TASK_ID}"
}
EOF

umoci insert --image ${NAME}:final version.json /app/version.json

echo "=== Pushing to docker hub ==="
export DOCKER_ARCHIVE_TAG="${DOCKER_TAG}-${VERSION}-$(date +%Y%m%d%H%M%S)-${VCS_HEAD_REV}"


skopeo copy oci:${NAME}:final docker://$DOCKER_REPO:$DOCKER_TAG
skopeo copy oci:${NAME}:final docker://$DOCKER_REPO:$DOCKER_ARCHIVE_TAG
