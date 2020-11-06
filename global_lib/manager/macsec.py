# common
from common_lib.macsec import Address, Channel, Rule
from common_lib.topology import Edge
from common_lib.logger import Logger
from common_lib.event import EventSystem

# global
from global_lib.manager import LLDPManager
from global_lib.local.controller import LocalController

# other
from os import urandom
from typing import Tuple, cast
from datetime import datetime, timedelta
from macsec_pb2 import bddp_key # type: ignore

class MacsecManager:
    def __init__(self,
            logger: Logger,
            lldp_manager: LLDPManager,
            event_system: EventSystem
        ):
        self._logger = logger
        self._lldp_manager = lldp_manager
        self._event_system = event_system
        # TODO save which port has which key

    def add(self, edge: Edge) -> None:
        """ Write protect and validate rules in both switches. """
        self._logger.info("Add macsec rules for " + str(edge))
        try:
            controller1, controller2 = self._get_controllers(edge)
            rule1, rule2 = self._create_rules(edge)
            controller1.get_service("macsec").add(rule1)
            controller2.get_service("macsec").add(rule2)

        except Exception as e:
            # Rollback
            self._logger.error("Could not write macsec rules for " + str(edge))
            self._logger.error(str(e))
            self.remove(edge)


    def remove(self, edge: Edge) -> None:
        """ Remove protect and validate rules in both switches. """
        self._logger.info("Remove macsec rules for " + str(edge))
        controller1, controller2 = self._get_controllers(edge)

        address1 = Address(controller1.get_mac(), edge.get_port2())
        address2 = Address(controller2.get_mac(), edge.get_port1())

        try:
            if not controller1.is_client():
                controller1.get_service("macsec").remove(address2)
        except:
            self._logger.warn("Could not remove macsec rules for controller " + \
                    controller1.get_name())
        try:
            if not controller2.is_client():
                controller2.get_service("macsec").remove(address1)
        except:
            self._logger.warn("Could not remove macsec rules for controller " + \
                    controller2.get_name())

    def _get_controllers(self, edge: Edge) -> Tuple[ LocalController, LocalController ]:
        controller1, controller2 = self._lldp_manager.get_edge_controllers(edge)
        return cast(LocalController, controller1), cast(LocalController, controller2)

    def _create_rules(self, edge: Edge) -> Tuple[ Rule, Rule ]:
        controller1, controller2 = self._get_controllers(edge)

        key1 = urandom(16)
        key2 = urandom(16)

        address1 = Address(controller1.get_mac(), edge.get_port2())
        address2 = Address(controller2.get_mac(), edge.get_port1())
        validate1 = Channel(key1, address2)
        protect1 = Channel(key2, address2)
        rule1 = Rule(
            validate1,
            protect1,
            1000,
            5000,
            datetime.now() + timedelta(seconds=30),
            datetime.now() + timedelta(seconds=60),
            edge,
            peer=Address(controller2.get_mac(), edge.get_port2())
        )
        validate2 = Channel(key2, address1)
        protect2 = Channel(key1, address1)
        rule2 = Rule(
            validate2,
            protect2,
            1000,
            5000,
            datetime.now() + timedelta(seconds=30),
            datetime.now() + timedelta(seconds=60),
            edge,
            peer=Address(controller1.get_mac(), edge.get_port1())
        )

        return rule1, rule2

    def renew(self, edge: Edge) -> None:
        self._logger.info("Renew macsec rules for " + str(edge))

        if self._lldp_manager.get_topology().has(edge):
            controller1, controller2 = self._get_controllers(edge)
            rule1, rule2 = self._create_rules(edge)
            controller1.get_service("macsec").renew(rule1)
            controller2.get_service("macsec").renew(rule2)

    def start(self):
        self._lldp_manager.register_add_connection(self.add)
        self._lldp_manager.register_remove_connection(self.remove)

    def teardown(self):
        self._lldp_manager.unregister_add_connection(self.add)
        self._lldp_manager.unregister_remove_connection(self.remove)

    def request_rule(self, edge: Edge) -> Rule:
        self._logger.info("Request rule for {edge}".format(edge=edge))

        controller1, controller2 = self._lldp_manager.get_edge_controllers(edge)
        rule1, rule2 = self._create_rules(edge)

        if controller1.is_client():
            controller2.get_service("macsec").add(rule2)
            return rule1

        if controller2.is_client():
            controller1.get_service("macsec").add(rule1)
            return rule2

        raise Exception("One controller must be a client.")

    def remove_rule(self, edge: Edge) -> None:
        self.remove(edge)

    def renew_rule(self, edge: Edge) -> Rule:
        self._logger.info("Renew macsec rules for " + str(edge))

        if self._lldp_manager.get_topology().has(edge):
            controller1, controller2 = self._get_controllers(edge)
            rule1, rule2 = self._create_rules(edge)
            if not controller1.is_client():
                controller1.get_service("macsec").renew(rule1)
                return rule2
            if not controller2.is_client():
                controller2.get_service("macsec").renew(rule2)
                return rule1
        raise Exception("One controller must be a client.")

    def send_bddp_packets(self, request: bddp_key) -> None:
        for controller in self._lldp_manager.get_controllers():
            if not controller.is_client():
                controller.get_service("macsec").send_bddp_packet(request)

