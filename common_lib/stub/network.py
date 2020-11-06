# common
from common_lib.ipsec import Endpoint

# protobuf / grpc
from ipsec_pb2_grpc import NetworkStub # type: ignore
from grpc import Channel # type: ignore

class Network:
    def __init__(self, channel: Channel):
        self._stub = NetworkStub(channel)

    def add_endpoint(self, endpoint: Endpoint) -> None:
        self._stub.add_endpoint(endpoint.to_proto())

    def remove_endpoint(self, endpoint: Endpoint) -> None:
        self._stub.remove_endpoint(endpoint.to_proto())
