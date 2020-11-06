# common
from common_lib.topology import Edge

# grpc / protobuf
from macsec_pb2_grpc import GlobalMacsecStub # type: ignore
from grpc import Channel # type: ignore

class Macsec:

    def __init__(self, channel: Channel) -> None:
        self._stub = GlobalMacsecStub(channel)

    def notify_soft_packet_limit(self, edge: Edge) -> None:
        self._stub.notify_soft_packet_limit(edge.to_proto())

    def notify_soft_time_limit(self, edge: Edge) -> None:
        self._stub.notify_soft_time_limit(edge.to_proto())
