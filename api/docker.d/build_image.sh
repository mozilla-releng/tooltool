#/bin/sh
set -e

test $DOCKER_REPO
test $DOCKER_TAG

cp ./src/tooltool_api/static/${FRONTEND_CONFIG} ./src/tooltool_api/static/config.mjs

docker build -f Dockerfile -t $DOCKER_REPO:$DOCKER_TAG .
docker save $DOCKER_REPO:$DOCKER_TAG > $1
