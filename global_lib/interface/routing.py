# common
from common_lib.server import synchronize, traceback, lazy
from common_lib.services import Service
from common_lib.logger import Logger
from common_lib.event import EventSystem

# global
from global_lib.manager import RoutingManager

# protobuf / grpc
from routing_pb2_grpc import GlobalRoutingServicer, add_GlobalRoutingServicer_to_server # type: ignore
from routing_pb2 import subnet # type: ignore
from nothing_pb2 import nothing # type: ignore
from grpc import ServicerContext # type: ignore

# other
from ipaddress import ip_network
from uuid import UUID

class RoutingService(Service, GlobalRoutingServicer):

    def __init__(self, \
            event_system: EventSystem, \
            logger: Logger, \
            routing_manager: RoutingManager \
        ):
        Service.__init__(self, add_GlobalRoutingServicer_to_server, event_system)

        self._logger = logger
        self._routing_manager = routing_manager

    @traceback("_logger")
    @synchronize
    def add_subnet(self, request: subnet, context: ServicerContext) -> nothing:
        self._routing_manager.add_subnet(UUID(request.controller_id),
                ip_network(request.subnet))
        return nothing()

    @traceback("_logger")
    @synchronize
    def remove_subnet(self, request: subnet, context: ServicerContext) -> nothing:
        self._routing_manager.remove_subnet(UUID(request.controller_id),
                ip_network(request.subnet))
        return nothing()

