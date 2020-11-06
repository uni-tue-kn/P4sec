# common
from common_lib.server import synchronize, traceback
from common_lib.services import Service
from common_lib.logger import Logger
from common_lib.event import EventSystem
from common_lib.ipsec import Tunnel

# protobuf / grpc
from ipsec_pb2_grpc import add_IpsecServicer_to_server, IpsecServicer # type: ignore
from ipsec_pb2 import tunnel # type: ignore
from nothing_pb2 import nothing # type: ignore
from grpc import ServicerContext # type: ignore
from wan_lib.manager import NetworkManager

class IpsecService(Service, IpsecServicer):

    def __init__(self,
            event_system: EventSystem,
            logger: Logger,
            network_manager: NetworkManager
        ):
        Service.__init__(self, add_IpsecServicer_to_server, event_system)
        self._logger = logger
        self._network_manager = network_manager

    @traceback("_logger")
    def notify_soft_packet_limit(self, request: tunnel, context: ServicerContext) -> nothing:
        self._logger.debug("soft packet limit reached")
        self._network_manager.renew(Tunnel.from_proto(request))
        return nothing()

    @traceback("_logger")
    def notify_hard_packet_limit(self, request: tunnel, context: ServicerContext) -> nothing:
        self._logger.debug("hard packet limit reached")
        self._network_manager.remove(Tunnel.from_proto(request))
        return nothing()
