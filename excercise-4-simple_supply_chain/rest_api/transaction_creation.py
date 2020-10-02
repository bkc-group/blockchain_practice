import hashlib
import logging

from sawtooth_rest_api.protobuf import batch_pb2
from sawtooth_rest_api.protobuf import transaction_pb2

import addresser
from protobuf import payload_pb2
from utils import *


def make_create_agent_transaction(transaction_signer, batch_signer, name, role, timestamp):
    print('=== make create agent transaction ===')
    agent_address = addresser.get_agent_address(
        transaction_signer.get_public_key().as_hex()
    )

    inputs = [agent_address]

    outputs = [agent_address]

    action = payload_pb2.CreateAgentAction(name=name, role=role)

    payload = payload_pb2.SupplyPayload(
        action=payload_pb2.SupplyPayload.CREATE_AGENT,
        create_agent=action,
        timestamp=timestamp)
    payload_bytes = payload.SerializeToString()

    return _make_batch(
        payload_bytes=payload_bytes,
        inputs=inputs,
        outputs=outputs,
        transaction_signer=transaction_signer,
        batch_signer=batch_signer)


def make_create_item_transaction(transaction_signer, batch_signer, item_id, latitude, longitude, timestamp):
    fprint('=== makde create item transaction ===')
    agent_address = addresser.get_agent_address(transaction_signer.get_public_key().as_hex())
    fprint(f'=== itemid: {item_id}')
    item_address = addresser.get_item_address(item_id)
    inputs = [agent_address, item_address]
    outputs = [item_address]

    action = payload_pb2.CreateItemAction(item_id=item_id, latitude=latitude, longitude=longitude)
    payload = payload_pb2.SupplyPayload(
        action=payload_pb2.SupplyPayload.CREATE_ITEM,
        create_item=action,
        timestamp=timestamp
    )

    payload_bytes = payload.SerializeToString()

    return _make_batch(
        payload_bytes=payload_bytes,
        inputs=inputs,
        outputs=outputs,
        transaction_signer=transaction_signer,
        batch_signer=batch_signer
    )


def make_update_item_transaction(transaction_signer, batch_signer, item_id, latitude, longitude, timestamp):
    agent_address = addresser.get_agent_address(transaction_signer.get_public_key().as_hex())
    item_address = addresser.get_item_address(item_id)

    inputs = [agent_address, item_address]
    outputs = [item_address]

    action = payload_pb2.UpdateItemAction(item_id=item_id, latitude=latitude, longitude=longitude)
    payload = payload_pb2.SupplyPayload(
        action=payload_pb2.SupplyPayload.UPDATE_ITEM,
        update_item=action,
        timestamp=timestamp
    )

    payload_bytes = payload.SerializeToString()
    return _make_batch(
        payload_bytes=payload_bytes,
        inputs=inputs,
        outputs=outputs,
        transaction_signer=transaction_signer,
        batch_signer=batch_signer
    )


def make_tranfer_item_transaction(
    transaction_signer, batch_signer, item_id, received_agent, timestamp):
    agent_address = addresser.get_agent_address(transaction_signer.get_public_key().as_hex())
    received_agent_address = addresser.get_agent_address(received_agent)
    item_address = addresser.get_item_address(item_id)

    inputs = [agent_address, item_address, received_agent_address]
    outputs = [item_address]
    action = payload_pb2.TranferItemAction(item_id=item_id, received_agent=received_agent_address)
    payload = payload_pb2.SupplyPayload(
        action=payload_pb2.SupplyPayload.TRANFER_ITEM,
        tranfer_item=action,
        timestamp=timestamp
    )
    payload_bytes = payload.SerializeToString()
    return _make_batch(
        payload_bytes=payload_bytes,
        inputs=inputs,
        outputs=outputs,
        transaction_signer=transaction_signer,
        batch_signer=batch_signer
    )


def _make_batch(payload_bytes, inputs, outputs, transaction_signer, batch_signer):

    transaction_header = transaction_pb2.TransactionHeader(
        family_name=addresser.FAMILY_NAME,
        family_version=addresser.FAMILY_VERSION,
        inputs=inputs,
        outputs=outputs,
        signer_public_key=transaction_signer.get_public_key().as_hex(),
        batcher_public_key=batch_signer.get_public_key().as_hex(),
        dependencies=[],
        payload_sha512=hashlib.sha512(payload_bytes).hexdigest())
    transaction_header_bytes = transaction_header.SerializeToString()

    transaction = transaction_pb2.Transaction(
        header=transaction_header_bytes,
        header_signature=transaction_signer.sign(transaction_header_bytes),
        payload=payload_bytes)

    batch_header = batch_pb2.BatchHeader(
        signer_public_key=batch_signer.get_public_key().as_hex(),
        transaction_ids=[transaction.header_signature])
    batch_header_bytes = batch_header.SerializeToString()

    batch = batch_pb2.Batch(
        header=batch_header_bytes,
        header_signature=batch_signer.sign(batch_header_bytes),
        transactions=[transaction]
    )

    return batch
