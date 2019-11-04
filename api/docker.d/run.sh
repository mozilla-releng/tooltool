#!/bin/bash
set -e

pushd `dirname $0` &>/dev/null
MY_DIR=$(pwd)
popd &>/dev/null

EXTRA_ARGS=""

# TODO: we might want to reverse this
if [ "$ENV" == "localdev" ]
then
    # TODO
    # TODO: provide default values
    test $HOST
    test $PORT

    # TODO: generate certificate if it does not exists
    cert="${MY_DIR}/cert.pem"
    key="${MY_DIR}/key.pem"

    # Local development only - we don't want these in deployed environments
    EXTRA_ARGS="--bind $HOST:$PORT --workers 3 --timeout 3600 --reload --reload-engine=poll --certfile=$cert --keyfile=$key"
fi

exec gunicorn tooltool_api.flask:app --log-file - $EXTRA_ARGS
