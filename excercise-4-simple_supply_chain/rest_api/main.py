import logging
import asyncio
import argparse
import logging
import sys

import aiohttp_cors
from aiohttp import web
from zmq.asyncio import ZMQEventLoop
from sawtooth_sdk.processor.log import init_console_logging

from router_handler import RouterHandler
from messaging import Messenger
from database import Database
from config import *
from utils import *


logging.basicConfig(filename="logFile.txt",
                    filemode='a',
                    format='%(asctime)s %(levelname)s-%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(logging.INFO)


def parse_args(args):
    parser = argparse.ArgumentParser(
        description='Starts the Simple Supply REST API')

    parser.add_argument(
        '-B', '--bind',
        help='identify host and port for api to run on',
        default='localhost:8000')
    parser.add_argument(
        '-C', '--connect',
        help='specify URL to connect to a running validator',
        default='tcp://localhost:4004')
    parser.add_argument(
        '-t', '--timeout',
        help='set time (in seconds) to wait for a validator response',
        default=500)
    parser.add_argument(
        '--db-name',
        help='The name of the database',
        default='simple-supply')
    parser.add_argument(
        '--db-host',
        help='The host of the database',
        default='localhost')
    parser.add_argument(
        '--db-port',
        help='The port of the database',
        default='5432')
    parser.add_argument(
        '--db-user',
        help='The authorized user of the database',
        default='sawtooth')
    parser.add_argument(
        '--db-password',
        help="The authorized user's password for database access",
        default='sawtooth')
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help='enable more verbose output to stderr')

    return parser.parse_args(args)


def init_api(messenger, database):
    loop = asyncio.get_event_loop()
    
    asyncio.ensure_future(database.connect())
    # database.create_tables()
    app = web.Application(client_max_size=AppConfig.CLIENT_MAX_SIZE)
    app['aes_key'] = 'ffffffffffffffffffffffffffffffff'
    app['secret_key'] = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'

    routes = web.RouteTableDef()
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    messenger.open_validator_connection()

    router_handler = RouterHandler(loop, messenger, database)
    app.router.add_post('/v1/signup', router_handler.create_agent)   # need to check output
    app.router.add_post('/v1/createItem', router_handler.create_item)   # need to check output
    app.router.add_post('/v1/tranferItem', router_handler.tranfer_item)   # need to check output
    app.router.add_post('/v1/updateItem', router_handler.update_item)   # need to check output

    web.run_app(app, host=AppConfig.HOST, port=AppConfig.PORT)


def main():
    loop = ZMQEventLoop()
    asyncio.set_event_loop(loop)

    try:
        opts = parse_args(sys.argv[1:])

        init_console_logging(verbose_level=opts.verbose)

        validator_url = opts.connect
        if 'tcp://' not in validator_url:
            validator_url = 'tcp://' + validator_url
        messenger = Messenger(validator_url)

        database = Database(
            opts.db_host,
            opts.db_port,
            opts.db_name,
            opts.db_user,
            opts.db_password,
            loop)
        try:
            host, port = opts.bind.split(':')
            port = int(port)
        except ValueError:
            print(f'Unable to parse binding {opts.bind}: Must be in the format host:port')
            sys.exit(1)

        init_api(messenger, database)
    except Exception as err:  # pylint: disable=broad-except
        # LOGGER.exception(err)
        fprint('err exe: ')
        fprint(err)
        sys.exit(1)
    finally:
        # database.disconnect()
        messenger.close_validator_connection()

main()