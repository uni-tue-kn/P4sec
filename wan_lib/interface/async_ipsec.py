# common
from common_lib.services import Service
from common_lib.server import synchronize, traceback
from common_lib.logger import Logger
from common_lib.event import EventSystem
from common_lib.ipsec import Tunnel

# wan
from wan_lib.manager import NetworkManager

# protobuf / grpc
from grpc import ServicerContext # type: ignore
from ipsec_pb2 import tunnel, tunnel_description # type: ignore
from ipsec_pb2_grpc import add_AsyncIpsecServicer_to_server, AsyncIpsecServicer # type: ignore
from nothing_pb2 import nothing # type: ignore

class AsyncIpsecService(Service, AsyncIpsecServicer):
    def __init__(self, \
            event_system: EventSystem, \
            logger: Logger, \
            network_manager: NetworkManager
        ):
        super().__init__(add_AsyncIpsecServicer_to_server, event_system)
        self._logger = logger
        self._network_manager = network_manager

    @traceback("_logger")
    @synchronize
    def request_tunnel(self, request: tunnel_description, context: ServicerContext) -> tunnel:
        tunnel = self._network_manager.async_connect(request)
        return tunnel.to_proto()

    @traceback("_logger")
    @synchronize
    def refresh_tunnel(self, request: tunnel, context: ServicerContext) -> tunnel:
        tunnel = self._network_manager.async_refresh_tunnel(Tunnel.from_proto(request))
        return tunnel.to_proto()

    @traceback("_logger")
    @synchronize
    def remove_tunnel(self, request: tunnel, context: ServicerContext) -> nothing:
        self._network_manager.async_remove_tunnel(Tunnel.from_proto(request))
        return nothing()
