from json.decoder import JSONDecodeError
import datetime
import time

from aiohttp.web import json_response
from itsdangerous import BadSignature
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from errors import *
from utils import *


class RouterHandler:
    def __init__(self, loop, messenger, database):
        self._loop = loop
        self._messenger = messenger
        self._database = database
        # self._database.create_tables()

    async def create_agent(self, request):
        fprint('=== create agent ===')
        body = await decode_request(request)
        required_fields = ['name', 'role']
        validate_fields(required_fields, body)
        name = body.get('name')
        role = body.get('role')
        public_key, private_key = self._messenger.get_new_key_pair()
        fprint(public_key)
        fprint('=== private key ===')
        fprint(private_key)
        await self._database.create_auth_entry(
            public_key, private_key, name)

        await self._messenger.send_create_agent_transaction(
            private_key=private_key,
            name=name,
            role=role,
            timestamp=get_time()
        )

        token = generate_auth_token(request.app['secret_key'], public_key)

        return json_response({'authorization': token})

    async def create_item(self, request):
        body = await decode_request(request)
        item_id = body.get('id')
        latitude = body.get('latitude')
        longitude = body.get('longitude')
        owner_name = body.get('owner_name')
        fprint(f'start creating a new item: {item_id}, {latitude}, {longitude}')

        agent = await self._database.fetch_agent_resource(owner_name)
        fprint(agent)
        private_key = agent['private_key']
        fprint(agent)

        await self._messenger.send_create_item_transaction(
            private_key=private_key,
            item_id=item_id,
            latitude=latitude,
            longitude=longitude,
            timestamp=get_time()
        )
        fprint('=== complete create item ===')
        return json_response({'data': 'Create document transaction submitted'})

    async def update_item(self, request):
        body = await decode_request(request)
        item_id = body.get('id')
        latitude = body.get('latitude')
        longitude = body.get('longitude')
        owner_name = body.get('owner_name')
        fprint(f'start updating a item: {item_id}, {latitude}, {longitude}')
        agent = await self._database.fetch_agent_resource(owner_name)
        private_key = agent['private_key']

        await self._messenger.send_update_item_transaction(
            private_key=private_key,
            item_id=item_id,
            latitude=latitude,
            longitude=longitude,
            timestamp=get_time()
        )
        return json_response({'data': 'Update item transaction submitted'})
    
    async def tranfer_item(self, request):
        body = await decode_request(request)
        item_id = body.get('item_id')
        received_agent_name = body.get('received_agent_name')
        received_agent = await self._database.fetch_agent_resource(received_agent_name)
        fprint('=====')
        fprint(received_agent)
        public_key = received_agent['public_key']
        fprint(public_key)

        owner_name = body.get('owner_name')
        owner_agent = await self._database.fetch_agent_resource(owner_name)
        private_key = owner_agent['private_key']

        fprint(f'Start tranfering item : {item_id} for user {received_agent}')
        await self._messenger.send_tranfer_item_transaction(
            private_key=private_key,
            item_id=item_id,
            received_agent=public_key,
            timestamp=get_time()
        )
        return json_response({'data': 'Tranfer item transaction submitted'})

async def decode_request(request):
    try:
        return await request.json()
    except JSONDecodeError:
        raise ApiBadRequest('Improper JSON format')


def validate_fields(required_fields, body):
    for field in required_fields:
        if body.get(field) is None:
            raise ApiBadRequest(
                "'{}' parameter is required".format(field))

def get_time():
    dts = datetime.datetime.utcnow()
    return round(time.mktime(dts.timetuple()) + dts.microsecond/1e6)

def generate_auth_token(secret_key, public_key):
    serializer = Serializer(secret_key)
    token = serializer.dumps({'public_key': public_key})
    return token.decode('ascii')