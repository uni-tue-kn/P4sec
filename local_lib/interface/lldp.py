# common
from common_lib.server import synchronize, traceback
from common_lib.services import Service
from common_lib.logger import Logger
from common_lib.event import EventSystem
from common_lib.topology import Edge

# local
from local_lib.manager import TopologyManager

# protobuf
from topology_pb2_grpc import add_LLDPServicer_to_server, LLDPServicer # type: ignore
from topology_pb2 import edge # type: ignore
from nothing_pb2 import nothing # type: ignore
from grpc import ServicerContext # type: ignore

class LLDPService(Service, LLDPServicer):

    def __init__(self, \
            event_system: EventSystem, \
            logger: Logger, \
            topology_manager: TopologyManager \
        ):
        Service.__init__(self, add_LLDPServicer_to_server, event_system)
        self._logger = logger
        self._topology_manager = topology_manager

    @traceback("_logger")
    @synchronize
    def add_edge(self, request: edge, context: ServicerContext) -> nothing:
        edge = Edge.from_proto(request)
        self._topology_manager.add_local_edge(edge)
        return nothing()

    @traceback("_logger")
    @synchronize
    def remove_edge(self, request: edge, context: ServicerContext) -> nothing:
        edge = Edge.from_proto(request)
        self._topology_manager.remove_local_edge(edge)
        return nothing()
