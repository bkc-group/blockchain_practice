

import datetime
import time

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction

import addresser
from protobuf import payload_pb2
from payload import Payload
from state import State
from utils import *


SYNC_TOLERANCE = 60 * 5


class Handler(TransactionHandler):

    @property
    def family_name(self):
        return addresser.FAMILY_NAME

    @property
    def family_versions(self):
        return [addresser.FAMILY_VERSION]

    @property
    def namespaces(self):
        return [addresser.NAMESPACE]

    def apply(self, transaction, context):
        fprint('=== come to apply ===')
        header = transaction.header
        payload = Payload(transaction.payload)
        state = State(context)

        _validate_timestamp(payload.timestamp)
        fprint('=== payload.action ===')
        fprint(payload.data)

        if payload.action == payload_pb2.SupplyPayload.CREATE_AGENT:
            _create_agent(
                state=state,
                public_key=header.signer_public_key,
                payload=payload
            )
        elif payload.action == payload_pb2.SupplyPayload.CREATE_ITEM:
            _create_item(
                state=state,
                public_key=header.signer_public_key,
                payload=payload)
        elif payload.action == payload_pb2.SupplyPayload.UPDATE_ITEM:
            _update_item(
                state=state,
                public_key=header.signer_public_key,
                payload=payload)
        elif payload.action == payload_pb2.SupplyPayload.TRANFER_ITEM:
            _tranfer_item(
                state=state,
                public_key=header.signer_public_key,
                payload=payload)
        else:
            raise InvalidTransaction('Unhandled action')


def _create_agent(state, public_key, payload):

    if state.get_agent(public_key):
        raise InvalidTransaction(f'Agent with the public key {public_key} already exists')

    state.set_agent(
        public_key=public_key,
        name=payload.data.name,
        role=payload.data.role,
        timestamp=payload.timestamp)


def _create_item(state, public_key, payload):

    if state.get_agent(public_key) is None:
        raise InvalidTransaction('Agent with the public key {} does not exist'.format(public_key))

    if payload.data.item_id == '':
        raise InvalidTransaction('No item ID provided')

    if state.get_item(payload.data.item_id):
        raise InvalidTransaction('Identifier {} belongs to an existing item'.format(payload.data.item_id))

    state.set_item(
        public_key=public_key,
        item_id=payload.data.item_id,
        latitude=payload.data.latitude,
        longitude=payload.data.longitude,
        timestamp=payload.timestamp)
    fprint('complete set new document')


def _update_item(state, public_key, payload):
    fprint('start update document in processor')
    fprint(public_key)
    fprint('=== payload data ===')
    fprint(payload.data.item_id)
    if payload.data.item_id == '':
        raise InvalidTransaction('No item ID provided')

    item = state.get_item(payload.data.item_id)

    if not item:
        raise InvalidTransaction('Item with the id: {} does not exist'.format(payload.data.item_id))
    
    if not _validate_item_owner(signer_public_key=public_key, item=item):
        raise InvalidTransaction('The transaction signer is not owner of the item')
    fprint('=== payload ===')
    fprint(payload)
    fprint(type(payload))
    fprint('=== payload data ===')
    fprint(payload.data)
    fprint('=======')
    state.update_item(
        item_id=payload.data.item_id,
        latitude=payload.data.latitude,
        longitude=payload.data.longitude,
        timestamp=payload.timestamp
    )
    fprint('=== update item complete ===')


def _tranfer_item(state, public_key, payload):
    fprint('=== payload data ===')
    fprint(payload.data)
    fprint('=======')
    if state.get_agent(public_key) is None:
        raise InvalidTransaction(
            'Agent with the public key {} does not exist'.format(public_key))
    fprint('get agent with shared_user_id complete !!!')
    item = state.get_item(payload.data.item_id)

    if item is None:
        raise InvalidTransaction('Item with the id {} does not exist'.format(payload.data.item_id))

    if not _validate_item_owner(signer_public_key=public_key, item=item):
        raise InvalidTransaction(
            'Transaction signer is not the owner of the item')

    state.tranfer_item(
        received_agent=payload.data.received_agent,
        item_id=payload.data.item_id,
        timestamp=payload.timestamp)


def _validate_item_owner(signer_public_key, item):
    """
    Validates that the public key of the signer is the latest (i.e.current) owner of the document
    """
    latest_owner = max(item.owners, key=lambda obj: obj.timestamp).public_key
    fprint('=== latest owner ===')
    fprint(latest_owner)
    fprint('=== signer public key ===')
    fprint(signer_public_key)
    return latest_owner == signer_public_key


def _validate_timestamp(timestamp):
    """
    Validates that the client submitted timestamp for a transaction is not greater than current time, within a 
    tolerance defined by SYNC_TOLERANCE

    NOTE: Timestamp validation can be challenging since the machines that are submitting and validating transactions 
    may have different system times
    """

    dts = datetime.datetime.utcnow()
    current_time = round(time.mktime(dts.timetuple()) + dts.microsecond/1e6)
    if (timestamp - current_time) > SYNC_TOLERANCE:
        raise InvalidTransaction(
            ' Timestamp must be less than local time.'
            ' Expected {0} in ({1}-{2}, {1}+{2})'.format( timestamp, current_time, SYNC_TOLERANCE))

