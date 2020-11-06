# common
from common_lib.topology import Edge

# grpc / protobuf
from topology_pb2_grpc import LLDPStub # type: ignore
from grpc import Channel # type: ignore

class LLDP:

    def __init__(self, channel: Channel) -> None:
        self._stub = LLDPStub(channel)

    def add_edge(self, edge: Edge) -> None:
        self._stub.add_edge(edge.to_proto())

    def remove_edge(self, edge: Edge) -> None:
        self._stub.remove_edge(edge.to_proto())
