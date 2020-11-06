# common
from common_lib.server import synchronize, traceback
from common_lib.services import Service
from common_lib.logger import Logger
from common_lib.event import EventSystem

# wan
from wan_lib.manager import NetworkManager

# protobuf / grpc
from routing_pb2_grpc import WanRoutingServicer, add_WanRoutingServicer_to_server # type: ignore
from routing_pb2 import subnet # type: ignore
from nothing_pb2 import nothing # type: ignore
from grpc import ServicerContext # type: ignore

# other
from ipaddress import ip_network
from uuid import UUID

class RoutingService(Service, WanRoutingServicer):

    def __init__(self, \
            event_system: EventSystem, \
            logger: Logger, \
            network_manager: NetworkManager \
        ):
        Service.__init__(self, add_WanRoutingServicer_to_server, event_system)

        self._logger = logger
        self._network_manager = network_manager

    @traceback("_logger")
    @synchronize
    def add_subnet(self, request: subnet, context: ServicerContext) -> nothing:
        # TODO authenticate & authorize
        self._network_manager.add_subnet(UUID(request.controller_id),
                ip_network(request.subnet))
        return nothing()

    @traceback("_logger")
    @synchronize
    def remove_subnet(self, request: subnet, context: ServicerContext) -> nothing:
        # TODO authenticate & authorize
        self._network_manager.remove_subnet(UUID(request.controller_id),
                ip_network(request.subnet))
        return nothing()

