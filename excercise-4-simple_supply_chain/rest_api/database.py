import asyncio
import logging

import aiopg
import psycopg2
from psycopg2.extras import RealDictCursor
from utils import *


CREATE_BLOCK_STMTS = """
CREATE TABLE IF NOT EXISTS blocks (
    block_num  bigint PRIMARY KEY,
    block_id   varchar
);
"""


CREATE_AUTH_STMTS = """
CREATE TABLE IF NOT EXISTS auth (
    public_key            varchar PRIMARY KEY,
    hashed_password       varchar,
    encrypted_private_key varchar
)
"""


LATEST_BLOCK_NUM = """
SELECT max(block_num) FROM blocks
"""
LOGGER = logging.getLogger(__name__)


class Database(object):
    """Manages connection to the postgres database and makes async queries
    """
    def __init__(self, host, port, name, user, password, loop):
        self._dsn = 'dbname={} user={} password={} host={} port={}'.format(
            name, user, password, host, port)
        self._loop = loop
        self._conn = None

    async def connect(self, retries=5, initial_delay=1, backoff=2):
        """Initializes a connection to the database

        Args:
            retries (int): Number of times to retry the connection
            initial_delay (int): Number of seconds wait between reconnects
            backoff (int): Multiplies the delay after each retry
        """
        LOGGER.info('Connecting to database')

        delay = initial_delay
        for attempt in range(retries):
            try:
                self._conn = await aiopg.connect(
                    dsn=self._dsn, loop=self._loop, echo=True)
                LOGGER.info('Successfully connected to database')
                return

            except psycopg2.OperationalError:
                LOGGER.debug(
                    'Connection failed.'
                    ' Retrying connection (%s retries remaining)',
                    retries - attempt)
                await asyncio.sleep(delay)
                delay *= backoff

        self._conn = await aiopg.connect(
            dsn=self._dsn, loop=self._loop, echo=True)
        # self.create_tables()
        LOGGER.info('Successfully connected to database')
        fprint('Successfully connected to database')

    def disconnect(self):
        """Closes connection to the database
        """
        self._conn.close()

    async def create_auth_entry(self,
                                public_key,
                                private_key,
                                name):
        insert = """
        INSERT INTO auth (
            public_key,
            private_key,
            name
        )
        VALUES ('{}', '{}', '{}');
        """.format(
            public_key,
            private_key,
            name)

        async with self._conn.cursor() as cursor:
            await cursor.execute(insert)

        self._conn.commit()

    async def fetch_agent_resource(self, name):
        fetch = """
        SELECT public_key, name, private_key FROM auth
        WHERE name='{0}'
        """.format(name)

        async with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
            await cursor.execute(fetch)
            return await cursor.fetchone()

    async def fetch_all_agent_resources(self):
        fetch = """
        SELECT public_key, name, timestamp FROM agents
        WHERE ({0}) >= start_block_num
        AND ({0}) < end_block_num;
        """.format(LATEST_BLOCK_NUM)

        async with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
            await cursor.execute(fetch)
            return await cursor.fetchall()

    async def fetch_auth_resource(self, public_key):
        fetch = """
        SELECT * FROM auth WHERE public_key='{}'
        """.format(public_key)

        async with self._conn.cursor(cursor_factory=RealDictCursor) as cursor:
            await cursor.execute(fetch)
            return await cursor.fetchone()
