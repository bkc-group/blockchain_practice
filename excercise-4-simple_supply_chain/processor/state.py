import addresser

from protobuf import agent_pb2
from protobuf import item_pb2
from utils import *


class State(object):
    def __init__(self, context, timeout=2):
        self._context = context
        self._timeout = timeout

    def get_agent(self, public_key):
        address = addresser.get_agent_address(public_key)

        state_entries = self._context.get_state(
            addresses=[address], timeout=self._timeout
        )

        if state_entries:
            container = agent_pb2.AgentContainer()
            container.ParseFromString(state_entries[0].data)

            for user in container.entries:
                if user.public_key == public_key:
                    return user

    def set_agent(self, public_key, name, role, timestamp):
        user_address = addresser.get_agent_address(public_key)

        agent = agent_pb2.Agent(
            public_key=public_key,
            name=name,
            role=role
        )
        container = agent_pb2.AgentContainer()
        state_entries = self._context.get_state(
            addresses=[user_address], timeout=self._timeout)
        if state_entries:
            container.ParseFromString(state_entries[0].data)

        container.entries.extend([agent])
        data = container.SerializeToString()

        updated_state = {}
        updated_state[user_address] = data
        self._context.set_state(updated_state, timeout=self._timeout)

    def get_item(self, item_id):
        address = addresser.get_item_address(item_id)

        try:
            state_entries = self._context.get_state(
                addresses=[address], timeout=self._timeout)

            if state_entries:
                container = item_pb2.ItemContainer()
                container.ParseFromString(state_entries[0].data)
                for item in container.entries:

                    if item.item_id == item_id:
                        return item
        except:
            return None

    def set_item(self, public_key, item_id, latitude, longitude, timestamp):
        address = addresser.get_item_address(item_id)
        fprint(address)
        owner = item_pb2.Item.Owner(
            public_key=public_key,
            timestamp=timestamp
        )

        location = item_pb2.Item.Location(
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp
        )

        item = item_pb2.Item(
            item_id=item_id,
            locations=[location],
            owners=[owner]
        )

        container = item_pb2.ItemContainer()
        state_entries = self._context.get_state(addresses=[address], timeout=self._timeout)
        fprint('==== state_entries: {}'.format(state_entries))

        if state_entries:
            container.ParseFromString(state_entries[0].data)

        container.entries.extend([item])

        data = container.SerializeToString()
        fprint('data: {}'.format(data))
        updated_state = {}
        updated_state[address] = data
        self._context.set_state(updated_state, timeout=self._timeout)

    def update_item(self, item_id, latitude, longitude, timestamp):

        location = item_pb2.Item.Location(
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp
        )

        fprint('start update item in state 1')
        address = addresser.get_item_address(item_id)
        container = item_pb2.ItemContainer()
        state_entries = self._context.get_state(addresses=[address], timeout=self._timeout)
        fprint('start update item in state 2')
        if state_entries:
            container.ParseFromString(state_entries[0].data)
    
            for item in container.entries:
                fprint('=== item.item_id ===')
                fprint(item.item_id)
                fprint(item_id)
                if item.item_id == item_id:
                    item.locations.extend([location])
        fprint('start update item in state 3')
        data = container.SerializeToString()
        updated_state = {}
        updated_state[address] = data

        self._context.set_state(updated_state, timeout=self._timeout)
        fprint('start update item in state 4')

    def tranfer_item(self, received_agent, item_id, timestamp):
        fprint(f'{received_agent}, {item_id}, {timestamp}')

        fprint('start share item in state 1')
        item_address = addresser.get_item_address(item_id)
        received_agent_address = addresser.get_agent_address(received_agent)
        shared_owner = item_pb2.Item.Owner(
            public_key=received_agent_address,
            timestamp=timestamp
        )
        container = item_pb2.ItemContainer()
        state_entries = self._context.get_state(addresses=[item_address], timeout=self._timeout)
        fprint('start update document in state 2')
        if state_entries:
            container.ParseFromString(state_entries[0].data)
    
            for item in container.entries:
                if item.item_id == item_id:
                    item.owners.extend([shared_owner])
        fprint('start update document in state 3')
        data = container.SerializeToString()
        updated_state = {}
        updated_state[item_address] = data

        self._context.set_state(updated_state, timeout=self._timeout)
        fprint('start update document in state 4')
        pass
