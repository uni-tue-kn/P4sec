# common
from common_lib.ipaddress import Network

# local
from local_lib.global_.registration import Registration

# grpc / protobuf
from routing_pb2_grpc import GlobalRoutingStub # type: ignore
from routing_pb2 import subnet # type: ignore
from grpc import Channel # type: ignore

# other
from uuid import UUID

class Routing:

    def __init__(self, channel: Channel, registration: Registration) -> None:
        self._stub = GlobalRoutingStub(channel)
        self._registration = registration

    def _get_id(self) -> UUID:
        return self._registration.get_id()

    def add_subnet(self, network: Network) -> None:
        self._stub.add_subnet(subnet(controller_id = str(self._get_id()), subnet=str(network)))

    def remove_subnet(self, network: Network) -> None:
        self._stub.remove_subnet(subnet(controller_id = str(self._get_id()), subnet=str(network)))
