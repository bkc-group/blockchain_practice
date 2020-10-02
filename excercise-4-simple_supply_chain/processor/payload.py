from sawtooth_sdk.processor.exceptions import InvalidTransaction

from protobuf import payload_pb2


class Payload(object):

    def __init__(self, payload):
        self._transaction = payload_pb2.SupplyPayload()
        self._transaction.ParseFromString(payload)

    @property
    def action(self):
        return self._transaction.action

    @property
    def data(self):
        if self._transaction.HasField('create_agent') and \
            self._transaction.action == payload_pb2.SupplyPayload.CREATE_AGENT:
            return self._transaction.create_agent

        if self._transaction.HasField('create_item') and \
            self._transaction.action == payload_pb2.SupplyPayload.CREATE_ITEM:
            return self._transaction.create_item

        if self._transaction.HasField('update_item') and \
            self._transaction.action == payload_pb2.SupplyPayload.UPDATE_ITEM:
            return self._transaction.update_item

        if self._transaction.HasField('tranfer_item') and \
            self._transaction.action == payload_pb2.SupplyPayload.TRANFER_ITEM:
            return self._transaction.tranfer_item

        raise InvalidTransaction('Action does not match payload data')

    @property
    def timestamp(self):
        return self._transaction.timestamp