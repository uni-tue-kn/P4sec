# common
from common_lib.server import synchronize, traceback
from common_lib.services import Service
from common_lib.logger import Logger
from common_lib.event import EventSystem
from common_lib.topology import Edge
from common_lib.macsec import Address, Rule

# global
from global_lib.manager import MacsecManager

# protobuf / grpc
from macsec_pb2_grpc import GlobalMacsecServicer, add_GlobalMacsecServicer_to_server # type: ignore
from nothing_pb2 import nothing # type: ignore
from topology_pb2 import edge # type: ignore
from macsec_pb2 import rule, address, bddp_key # type: ignore
from grpc import ServicerContext # type: ignore

# other
from os import urandom

class MacsecService(Service, GlobalMacsecServicer):

    def __init__(self, \
            event_system: EventSystem, \
            logger: Logger, \
            macsec_manager: MacsecManager \
        ):
        Service.__init__(self, add_GlobalMacsecServicer_to_server, event_system)

        self._logger = logger
        self._macsec_manager = macsec_manager

    def notify_soft_packet_limit(self, request: edge, context: ServicerContext) -> nothing:
        edge = Edge.from_proto(request)
        self._macsec_manager.renew(edge)
        return nothing()

    def notify_soft_time_limit(self, request: edge, context: ServicerContext) -> nothing:
        edge = Edge.from_proto(request)
        self._macsec_manager.renew(edge)
        return nothing()

    @traceback("_logger")
    @synchronize
    def request_rule(self, request: edge, context: ServicerContext) -> rule:
        edge = Edge.from_proto(request)
        rule = self._macsec_manager.request_rule(edge)
        return rule.to_proto()

    @traceback("_logger")
    @synchronize
    def remove_rule(self, request: edge, context: ServicerContext) -> nothing:
        edge = Edge.from_proto(request)
        self._macsec_manager.remove_rule(edge)
        return nothing()

    @traceback("_logger")
    @synchronize
    def renew_rule(self, request: edge, context: ServicerContext) -> rule:
        edge = Edge.from_proto(request)
        rule = self._macsec_manager.renew_rule(edge)
        return rule.to_proto()

    @traceback("_logger")
    @synchronize
    def send_bddp_packet(self, request: bddp_key, context: ServicerContext) -> nothing:
        self._macsec_manager.send_bddp_packets(request)
        return nothing()
