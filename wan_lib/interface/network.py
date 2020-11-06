# common
from common_lib.services import Service
from common_lib.server import synchronize, traceback
from common_lib.logger import Logger
from common_lib.event import EventSystem
from common_lib.ipsec import Endpoint, Tunnel

# wan
from wan_lib.manager import NetworkManager

# protobuf / grpc
from grpc import ServicerContext # type: ignore
from ipsec_pb2 import endpoint, tunnel # type: ignore
from ipsec_pb2_grpc import add_NetworkServicer_to_server, NetworkServicer # type: ignore
from nothing_pb2 import nothing # type: ignore

class NetworkService(Service, NetworkServicer):
    def __init__(self, \
            event_system: EventSystem, \
            logger: Logger, \
            network_manager: NetworkManager
        ):
        super().__init__(add_NetworkServicer_to_server, event_system)
        self._logger = logger
        self._network_manager = network_manager

    @traceback("_logger")
    @synchronize
    def add_endpoint(self, request: endpoint, context: ServicerContext) -> nothing:
        endpoint = Endpoint.from_proto(request)
        self._network_manager.add_endpoint(endpoint)
        return nothing()

    @traceback("_logger")
    @synchronize
    def remove_endpoint(self, request: endpoint, context: ServicerContext) -> nothing:
        endpoint = Endpoint.from_proto(request)
        self._network_manager.remove_endpoint(endpoint)
        return nothing()
