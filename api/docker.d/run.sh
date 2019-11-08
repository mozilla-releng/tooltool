#!/bin/sh
set -e

pushd `dirname $0` &>/dev/null
MY_DIR=$(pwd)
popd &>/dev/null

EXTRA_ARGS=""

if [ "$ENV" == "localdev" ]
then
    CERT="${MY_DIR}/cert.pem"
    KEY="${MY_DIR}/key.pem"

    # generate certificate if it doesn't exists
    if [ ! -e "$KEY" ]; then
      exit 123;
      rm -f $CERT $KEY
      openssl req -x509 -newkey rsa:4096 -nodes -out $CERT -keyout $KEY -days 365
    fi

    # Local development only - we don't want these in deployed environments
    EXTRA_ARGS="--bind $HOST:$PORT --workers 3 --timeout 3600 --reload --reload-engine=poll --certfile=$CERT --keyfile=$KEY"
fi

exec gunicorn tooltool_api.flask:app --log-file - $EXTRA_ARGS
