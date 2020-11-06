# common
from common_lib.macsec import Rule, Address

# protobuf / grpc
from macsec_pb2_grpc import MacsecStub # type: ignore
from macsec_pb2 import bddp_key # type: ignore
from grpc import Channel # type: ignore

class Macsec:

    def __init__(self, channel: Channel):
        self._stub = MacsecStub(channel)

    def add(self, rule: Rule) -> None:
        self._stub.add(rule.to_proto())

    def remove(self, address: Address) -> None:
        self._stub.remove(address.to_proto())

    def renew(self, rule: Rule) -> None:
        self._stub.renew(rule.to_proto())

    def send_bddp_packet(self, key: bddp_key) -> None:
        self._stub.send_bddp_packet(key)
