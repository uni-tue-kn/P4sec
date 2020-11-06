# common
from common_lib.logger import Logger
from common_lib.macsec import Rule, Address
from common_lib.topology import BDDPPacket, Edge

# client
from client_lib.settings import Settings
from client_lib.wan import WanController
from client_lib.global_ import GlobalController

# other
from os import system
from typing import List, Optional
from netifaces import ifaddresses, AF_INET # type: ignore
from scapy.all import sniff, Ether # type: ignore
from threading import Thread
from time import sleep

macsec = "ip link add link {interface} macsec0 type macsec"
macsec_del = "ip link del link {interface} macsec0"

protect = "ip macsec add macsec0 tx sa 0 pn {soft_packet_limit} key 01 {key}"
# the delete rule is here for completeness -> it doesn not work in a namespace
protect_del = "ip macsec del macsec0 tx sa 0"

set_mac = "ip macsec add macsec0 rx port 1 address {mac}"
validate = "ip macsec add macsec0 rx address {mac} port {port} sa 0 pn {pn} key 02 {key}"
# the delete rule is here for completeness -> it doesn not work in a namespace
validate_del = "ip macsec del macsec0 rx address {mac} port {port} sa 0"

class MacsecManager:

    def __init__(self,
            logger: Logger,
            settings: Settings,
            wan_controller: WanController,
            global_controller: GlobalController
        ) -> None:
        self._logger = logger
        self._settings = settings
        self._wan_controller = wan_controller
        self._global_controller = global_controller
        self._rules = [ ] # type: List[ Rule ]
        self._rule = None # type: Optional[ Rule ]
        self._interface = self._settings.get_interface()
        self._addresses = [ x["addr"] for x in ifaddresses(self._interface)[AF_INET] ]
        self._port = 1 # this is always 1
        self._edge = None # type: Optional[ Edge ]

    def _run_command(self, command: str) -> None:
        self._logger.debug("run command: " + command, 2)

        status = system(command)

        if status is not 0:
            self._logger.error("Command failed with exit code: " + str(status))

    def new(self, rule: Rule) -> None:
        self._global_controller.unconnect()
        self._logger.info("Install macsec rule: {rule}".format(rule=rule))

        peer = rule.get_peer()

        self._rule = rule
        self._run_command("ip link add link {interface} macsec0 type macsec encrypt on"
                .format(interface=self._interface))

        self._run_command("ip macsec add macsec0 rx port {port} address {mac}"
                .format(port = peer.get_port(),
                    mac = rule.get_validate().get_address().get_mac()))

        self._run_command("ip macsec add macsec0 tx sa 0 pn 1 on key 00 {key}"
                .format(key = rule.get_protect().get_key().hex()))
        self._run_command("ip macsec add macsec0 rx port {port} address {mac} sa 0 pn 1 on key 01 {key}"
                .format(key = rule.get_validate().get_key().hex(),
                    port = peer.get_port(),
                    mac = rule.get_validate().get_address().get_mac()))
        for address in self._addresses:
            self._run_command("ip a del {addr}/24 dev {interface}".format(addr=address,
                interface=self._interface))
            self._run_command("ip a add {addr}/24 dev macsec0".format(addr=address))

        self._run_command("ip link set macsec0 up")
        self._run_command("ip route add default via 10.0.1.254")
        self._global_controller.reconnect()

    def renew(self, rule: Rule) -> None:
        pass

    def remove(self, rule: Rule) -> None:
        # This is a hack
        # It is not possible to delete macsec rules in a network namespace
        # -> Remove interface and add it again, then add all rules
        self._run_command("ip link del macsec0")

        for rule in self._rules:
            pass

        for address in self._addresses:
            self._run_command("ip a add {addr}/24 dev {interface}".format(
                addr=address, interface=self._interface))

        self._run_command("ip route add default via 10.0.1.254")
        self._global_controller.get_service("macsec").remove_rule(self._edge)

    def handle_bddp(self, packet, bddp_key) -> None:
        ethernet = packet["Ether"]
        self._bddp = BDDPPacket.parse(ethernet, bddp_key)
        self._logger.debug("Got bddp packet {packet}".format(packet=self._bddp))

    def wait_for_bddp_packet(self, bddp_key) -> Thread:
        def waiter():
            self._logger.debug("Wait for bddp packet")
            sniff(filter="ether proto 0x8999",
                    prn=lambda packet: self.handle_bddp(packet, bddp_key), count=1)
        thread = Thread(target=waiter)
        thread.start()
        return thread

    def start(self) -> None:
        macsec = self._global_controller.get_service("macsec")

        # get bddp packet from switch
        key = BDDPPacket.generate_key()
        thread = self.wait_for_bddp_packet(key)
        sleep(1) #TODO use event
        macsec.send_bddp_packet(key)
        thread.join()

        self._edge = Edge(
            self._bddp.get_controller(),
            self._bddp.get_port(),
            self._global_controller.get_service("registration").get_id(),
            self._port
        )
        self.new(macsec.request_rule(self._edge))

    def stop(self) -> None:
        if self._rule is not None:
            self.remove(self._rule)
