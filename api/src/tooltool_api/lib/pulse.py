# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import datetime
import sys

import aioamqp
import flask
import kombu

import tooltool_api.lib.dockerflow
import tooltool_api.lib.log

logger = tooltool_api.lib.log.get_logger(__name__)

DEFAULT_CONFIG = dict(
    PULSE_HOST='pulse.mozilla.org',
    PULSE_PORT=5671,
    PULSE_VIRTUAL_HOST='/',
    PULSE_USE_SSL=True,
    PULSE_CONNECTION_TIMEOUT=5,
)


async def _create_consumer(user, password, exchange, topic, callback):
    '''
    Create an async consumer for Mozilla pulse queues
    Inspired by : https://github.com/mozilla-releng/fennec-aurora-task-creator/blob/master/fennec_aurora_task_creator/worker.py  # noqa
    '''
    assert isinstance(user, str)
    assert isinstance(password, str)
    assert isinstance(exchange, str)
    assert isinstance(topic, str)

    host = 'pulse.mozilla.org'
    port = 5671

    transport, protocol = await aioamqp.connect(
        host=host,
        login=user,
        password=password,
        ssl=True,
        port=port,
    )

    channel = await protocol.channel()
    await channel.basic_qos(
        prefetch_count=1,
        prefetch_size=0,
        connection_global=False
    )

    # get exchange name out from full exchange name
    exchange_name = exchange
    if exchange.startswith(f'exchange/{user}/'):
        exchange_name = exchange[len(f'exchange/{user}/'):]
    elif exchange.startswith(f'exchange/'):
        exchange_name = exchange[len(f'exchange/'):]

    # full exchange name should start with "exchange/"
    if not exchange.startswith('exchange/'):
        exchange = f'exchange/{exchange}'

    # queue is required to:
    # - start with "queue/"
    # - user should follow the "queue/"
    # - after that "exchange/" should follow, this is not requirement from
    #   pulse but something we started doing in release services
    queue = f'queue/{user}/exchange/{exchange_name}'

    await channel.queue_declare(queue_name=queue, durable=True)

    # in case we are going to listen to an exchange that is specific for this
    # user, we need to ensure that exchange exists before first message is
    # sent (this is what creates exchange)
    if exchange.startswith(f'exchange/{user}/'):
        await channel.exchange_declare(exchange_name=exchange,
                                       type_name='topic',
                                       durable=True)

    logger.info('Connected', queue=queue, topic=topic, exchange=exchange)

    await channel.queue_bind(exchange_name=exchange,
                             queue_name=queue,
                             routing_key=topic)
    await channel.basic_consume(callback, queue_name=queue)

    logger.info('Worker starts consuming messages')
    logger.info('Starting loop to ensure connection is open')
    while True:
        await asyncio.sleep(10)
        try:
            await protocol.ensure_open()
        # raise AmqpClosedConnection in case the connection is closed.
        except (aioamqp.AmqpClosedConnection, OSError):
            await protocol.close()
            transport.close()
            raise


async def create_consumer(user, password, exchange, topic, callback):
    while True:
        try:
            return await _create_consumer(user, password, exchange, topic, callback)
        except (aioamqp.AmqpClosedConnection, OSError):
            logger.exception('Reconnecting in 10 seconds')
            await asyncio.sleep(10)


def run_consumer(consumer):
    '''
    Helper to run indefinitely an asyncio consumer
    '''
    event_loop = asyncio.get_event_loop()

    try:
        event_loop.run_until_complete(consumer)
        event_loop.run_forever()
    except KeyboardInterrupt:
        # TODO: make better shutdown
        logger.exception('KeyboardInterrupt registered, exiting.')
        event_loop.stop()
        while event_loop.is_running():
            pass
        event_loop.close()
        sys.exit()


class Pulse(object):
    ''' Documentation about Pulse

        https://wiki.mozilla.org/Auto-tools/Projects/Pulse
        https://wiki.mozilla.org/Auto-tools/Projects/Pulse/Exchanges
    '''

    def __init__(self, host, port, user, password, virtual_host='/', ssl=True,
                 connect_timeout=5):
        self.connection = kombu.Connection(
            hostname=host,
            port=port,
            userid=user,
            password=password,
            virtual_host=virtual_host,
            ssl=ssl,
            connect_timeout=connect_timeout,
        )

    def ping(self):
        with self.connection as connection:
            if connection.connected:
                connection.close()
                connection.connect()
            else:
                connection.connect()
                connection.close()

    def publish(self, exchange_name, routing_key, payload):
        with self.connection as connection:
            if not connection.connected:
                connection.connect()

            exchange = kombu.Exchange(exchange_name, type='topic')
            message = {
                'payload': payload,
                '_meta': {
                    'exchange': exchange_name,
                    'routing_key': routing_key,
                    'serializer': 'json',
                    'sent': datetime.datetime.utcnow().isoformat()},
            }

            producer = connection.Producer(
                exchange=exchange,
                routing_key=routing_key,
                serializer='json',
            )
            producer.publish(message)
            connection.close()


def init_app(app):
    return Pulse(
        app.config.get('PULSE_HOST', DEFAULT_CONFIG['PULSE_HOST']),
        app.config.get('PULSE_PORT', DEFAULT_CONFIG['PULSE_PORT']),
        app.config.get('PULSE_USER'),
        app.config.get('PULSE_PASSWORD'),
        app.config.get('PULSE_VIRTUAL_HOST', DEFAULT_CONFIG['PULSE_VIRTUAL_HOST']),
        app.config.get('PULSE_USE_SSL', DEFAULT_CONFIG['PULSE_USE_SSL']),
        app.config.get('PULSE_CONNECTION_TIMEOUT', DEFAULT_CONFIG['PULSE_CONNECTION_TIMEOUT']),
    )


def app_heartbeat():
    try:
        flask.current_app.pulse.ping()
    except Exception as e:
        logger.exception(e)
        raise tooltool_api.lib.dockerflow.HeartbeatException('Cannot connect to pulse the service.')
