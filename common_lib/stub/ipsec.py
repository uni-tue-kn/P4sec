# common
from common_lib.ipsec import Tunnel
from common_lib.logger import Logger
from common_lib.stub.failable import failable

# protobuf / grpc
from ipsec_pb2_grpc import IpsecStub # type: ignore
from grpc import Channel # type: ignore

class Ipsec:

    def __init__(self, channel: Channel):
        self._stub = IpsecStub(channel)

    @failable("Ipse.new")
    def new(self, tunnel: Tunnel) -> None:
        self._stub.new(tunnel.to_proto())

    @failable("Ipse.renew")
    def renew(self, tunnel: Tunnel) -> None:
        self._stub.renew(tunnel.to_proto())

    @failable("Ipse.remove")
    def remove(self, tunnel: Tunnel) -> None:
        self._stub.remove(tunnel.to_proto())
