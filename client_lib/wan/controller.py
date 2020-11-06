# common
from common_lib.stub import StubController, Network, Registration

# client
from client_lib.settings import Settings

# grpc
from ipsec_pb2_grpc import AsyncIpsecStub # type: ignore

class WanController(StubController):
    def __init__(self, settings: Settings):
        wan = settings.get_wan()
        super().__init__("wan-controller", wan.get_address(), wan.get_credentials())
        self.add_service("network", Network)
        self.add_service("ipsec", AsyncIpsecStub)
