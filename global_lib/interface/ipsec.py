# common
from common_lib.server import synchronize, traceback
from common_lib.services import Service
from common_lib.logger import Logger
from common_lib.event import EventSystem
from common_lib.ipsec import Tunnel

# global
from global_lib.manager import IpsecManager

# protobuf / grpc
from ipsec_pb2_grpc import add_IpsecServicer_to_server, IpsecServicer # type: ignore
from ipsec_pb2 import tunnel # type: ignore
from nothing_pb2 import nothing # type: ignore
from grpc import ServicerContext # type: ignore
from global_lib.wan import WanController

class IpsecService(Service, IpsecServicer):

    def __init__(self,
            event_system: EventSystem,
            logger: Logger,
            ipsec_manager: IpsecManager,
            wan_controller: WanController
        ):
        Service.__init__(self, add_IpsecServicer_to_server, event_system)
        self._logger = logger
        self._ipsec_manager = ipsec_manager
        self._wan_controller = wan_controller

    @traceback("_logger")
    @synchronize
    def new(self, request: tunnel, context: ServicerContext) -> nothing:
        tunnel = Tunnel.from_proto(request)
        self._ipsec_manager.new(tunnel)
        return nothing()

    @traceback("_logger")
    @synchronize
    def renew(self, request: tunnel, context: ServicerContext) -> nothing:
        tunnel = Tunnel.from_proto(request)
        self._ipsec_manager.renew(tunnel)
        return nothing()

    @traceback("_logger")
    @synchronize
    def remove(self, request: tunnel, context: ServicerContext) -> nothing:
        tunnel = Tunnel.from_proto(request)
        self._ipsec_manager.remove(tunnel)
        return nothing()

    @traceback("_logger")
    def notify_soft_packet_limit(self, request: tunnel, context: ServicerContext) -> nothing:
        ipsec = self._wan_controller.get_service("ipsec")
        ipsec.notify_soft_packet_limit(Tunnel.from_proto(request))
        return nothing()

    @traceback("_logger")
    def notify_hard_packet_limit(self, request: tunnel, context: ServicerContext) -> nothing:
        ipsec = self._wan_controller.get_service("ipsec")
        ipsec.notify_hard_packet_limit(Tunnel.from_proto(request))
        return nothing()
