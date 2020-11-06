# protobuf / grpc
from general_pb2_grpc import GeneralStub # type: ignore
from nothing_pb2 import nothing # type: ignore
from grpc import Channel, RpcError # type: ignore

class General:

    def __init__(self, channel: Channel):
        self._stub = GeneralStub(channel)

    def is_connected(self) -> bool:
        try:
            self._stub.check_connection(nothing())
            return True
        except RpcError:
            return False

