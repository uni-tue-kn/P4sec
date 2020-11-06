# common
from common_lib.ipaddress import Address

# protobuf / grpc
from ipsec_pb2_grpc import ConcentratorStub # type: ignore
from ipsec_pb2 import address as proto_address # type: ignore
from grpc import Channel # type: ignore

class Concentrator:

    def __init__(self, channel: Channel):
        self._stub = ConcentratorStub(channel)

    def set_ip(self, address: Address) -> None:
        self._stub.set_ip(proto_address(value=str(address)))
