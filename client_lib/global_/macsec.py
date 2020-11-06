# common
from common_lib.topology import Edge
from common_lib.macsec import Rule, Address

# grpc / protobuf
from macsec_pb2_grpc import GlobalMacsecStub # type: ignore
from grpc import Channel # type: ignore
from macsec_pb2 import bddp_key # type: ignore

class Macsec:

    def __init__(self, channel: Channel) -> None:
        self._stub = GlobalMacsecStub(channel)

    def notify_soft_packet_limit(self, edge: Edge) -> None:
        self._stub.notify_soft_packet_limit(edge.to_proto())

    def notify_soft_time_limit(self, edge: Edge) -> None:
        self._stub.notify_soft_time_limit(edge.to_proto())

    def request_rule(self, edge: Edge) -> Rule:
        return Rule.from_proto(self._stub.request_rule(edge.to_proto()))

    def remove_rule(self, edge: Edge) -> None:
        self._stub.remove_rule(edge.to_proto())

    def renew_rule(self, edge: Edge) -> Rule:
        return Rule.from_proto(self._stub.renew_rule(edge.to_proto()))

    def send_bddp_packet(self, key: bytes) -> None:
        self._stub.send_bddp_packet(bddp_key(value=key))
