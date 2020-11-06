# common
from common_lib.server import synchronize, traceback
from common_lib.services import Service
from common_lib.logger import Logger
from common_lib.event import EventSystem

# local
from local_lib.manager import IpsecManager

# protobuf
from ipsec_pb2_grpc import add_ConcentratorServicer_to_server, ConcentratorServicer # type: ignore
from ipsec_pb2 import address # type: ignore
from nothing_pb2 import nothing # type: ignore
from grpc import ServicerContext # type: ignore

# other
from ipaddress import ip_address

class ConcentratorService(Service, ConcentratorServicer):

    def __init__(self,
            event_system: EventSystem,
            logger: Logger,
            ipsec_manager: IpsecManager
        ):
        Service.__init__(self, add_ConcentratorServicer_to_server, event_system)
        self._logger = logger
        self._ipsec_manager = ipsec_manager

    @traceback("_logger")
    @synchronize
    def set_ip(self, request: address, context: ServicerContext) -> nothing:
        self._ipsec_manager.set_ip(ip_address(request.value))
        return nothing()
