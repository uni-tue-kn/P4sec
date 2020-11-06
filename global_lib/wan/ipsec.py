# common
from common_lib.ipsec import Tunnel

# grpc / protobuf
from ipsec_pb2_grpc import IpsecStub # type: ignore
from grpc import Channel # type: ignore

class Ipsec:

    def __init__(self, channel: Channel) -> None:
        self._stub = IpsecStub(channel)

    def notify_soft_packet_limit(self, tunnel: Tunnel) -> None:
        self._stub.notify_soft_packet_limit(tunnel.to_proto())

    def notify_hard_packet_limit(self, tunnel: Tunnel) -> None:
        self._stub.notify_hard_packet_limit(tunnel.to_proto())
