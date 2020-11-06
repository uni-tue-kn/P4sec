# common
from common_lib.services import Service
from common_lib.server import synchronize, traceback
from common_lib.event import EventSystem
from common_lib.logger import Logger
from common_lib.routing import ForwardRule

# local
from local_lib.manager import RoutingManager

# protobuf / grpc
from routing_pb2_grpc import LocalRoutingServicer, add_LocalRoutingServicer_to_server # type: ignore
from nothing_pb2 import nothing # type: ignore
from routing_pb2 import forward_rule # type: ignore
from grpc import ServicerContext # type: ignore

class RoutingService(Service, LocalRoutingServicer):

    def __init__(self,
            event_system: EventSystem,
            logger: Logger,
            routing_manager: RoutingManager
            ) -> None:
        Service.__init__(self, add_LocalRoutingServicer_to_server, event_system)

        self._logger = logger
        self._routing_manager = routing_manager

    @traceback("_logger")
    @synchronize
    def new_forward_rule(self, request: forward_rule, context: ServicerContext) -> nothing:
        rule = ForwardRule.from_proto(request)
        self._routing_manager.new_forward_rule(rule)
        return nothing()

    @traceback("_logger")
    @synchronize
    def remove_forward_rule(self, request: forward_rule, context: ServicerContext) -> nothing:
        rule = ForwardRule.from_proto(request)
        self._routing_manager.remove_forward_rule(rule)
        return nothing()
