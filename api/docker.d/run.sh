#!/bin/bash
set -e

pushd `dirname $0` &>/dev/null
MY_DIR=$(pwd)
popd &>/dev/null

EXTRA_ARGS=""

if [ "$ENV" == "localdev" ]
then
    CERT="$MY_DIR/cert.pem"
    KEY="$MY_DIR/key.pem"

    # Local development only - we don't want these in deployed environments
    EXTRA_ARGS="--bind $HOST:$PORT --workers 3 --timeout 3600 --reload --reload-engine=poll --certfile=$CERT --keyfile=$KEY"
fi

exec gunicorn tooltool_api.flask:app --log-file - $EXTRA_ARGS
