#!/bin/sh
set -e

test $DOCKER_REPO
test $DOCKER_TAG
test $SECRET_URL
test $IMAGE_URL


echo "=== Generating dockercfg ==="
# docker login stopped working in Taskcluster for some reason
wget -qO- $SECRET_URL | jq '.secret.docker.dockercfg' > /root/.dockercfg
chmod 600 /root/.dockercfg

echo "==== Getting image ==="
wget -qO /workspace/image.tar.zst $IMAGE_URL
unzstd /workspace/image.tar.zst

echo "=== Pushing to docker hub ==="
skopeo --insecure-policy copy docker-archive:/workspace/image.tar docker://docker.io/$DOCKER_REPO:$DOCKER_TAG

echo "=== Clean up ==="
rm -f /root/.dockercfg
