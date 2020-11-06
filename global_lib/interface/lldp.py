# common
from common_lib.server import synchronize, traceback
from common_lib.services import Service
from common_lib.logger import Logger
from common_lib.event import EventSystem
from common_lib.topology import Edge

# global
from global_lib.manager import LLDPManager

# protobuf / grpc
from topology_pb2_grpc import LLDPServicer, add_LLDPServicer_to_server # type: ignore
from nothing_pb2 import nothing # type: ignore
from topology_pb2 import edge # type: ignore
from grpc import ServicerContext # type: ignore

# other
from os import urandom

class LLDPService(Service, LLDPServicer):

    def __init__(self, \
            event_system: EventSystem, \
            logger: Logger, \
            lldp_manager: LLDPManager \
        ):
        Service.__init__(self, add_LLDPServicer_to_server, event_system)

        self._logger = logger
        self._lldp_manager = lldp_manager

    @traceback("_logger")
    @synchronize
    def add_edge(self, request: edge, context: ServicerContext) -> nothing:
        edge = Edge.from_proto(request)
        self._logger.info("Adding edge: " + str(edge))
        self._lldp_manager.add(edge)
        return nothing()

    @traceback("_logger")
    @synchronize
    def remove_edge(self, request: edge, context: ServicerContext) -> nothing:
        edge = Edge.from_proto(request)
        self._logger.info("Removing edge: " + str(edge))
        self._lldp_manager.remove(edge)
        return nothing()

