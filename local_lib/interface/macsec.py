# common
from common_lib.server import synchronize, traceback
from common_lib.services import Service
from common_lib.logger import Logger
from common_lib.event import EventSystem
from common_lib.macsec import Address, Rule

# local
from local_lib.manager import MacsecManager

# protobuf
from macsec_pb2_grpc import add_MacsecServicer_to_server, MacsecServicer # type: ignore
from macsec_pb2 import rule, address, bddp_key # type: ignore
from nothing_pb2 import nothing # type: ignore
from grpc import ServicerContext # type: ignore

class MacsecService(Service, MacsecServicer):

    def __init__(self, event_system: EventSystem, logger: Logger, macsec_manager: MacsecManager):
        Service.__init__(self, add_MacsecServicer_to_server, event_system)
        self._logger = logger
        self._macsec_manager = macsec_manager

    @traceback("_logger")
    @synchronize
    def add(self, request: rule, context: ServicerContext) -> nothing:
        rule = Rule.from_proto(request)
        self._macsec_manager.add(rule)
        return nothing()

    @traceback("_logger")
    @synchronize
    def remove(self, request: address, context: ServicerContext) -> nothing:
        address = Address.from_proto(request)
        self._macsec_manager.remove(address)
        return nothing()

    @traceback("_logger")
    @synchronize
    def renew(self, request: rule, context: ServicerContext) -> nothing:
        rule = Rule.from_proto(request)
        self._macsec_manager.renew(rule)
        return nothing()

    @traceback("_logger")
    @synchronize
    def request_connection(self, request: address, context: ServicerContext) -> rule:
        address = Address.from_proto(request)
        rule = self._macsec_manager.request_rule(address)
        return rule.to_proto()

    def send_bddp_packet(self, key: bddp_key, context: ServicerContext) -> nothing:
        self._macsec_manager.send_bddp_packet(key)
        return nothing()
