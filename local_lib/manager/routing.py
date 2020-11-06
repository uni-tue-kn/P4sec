# common
from common_lib.logger import Logger
from common_lib.ipaddress import Address, Host, Network
from common_lib.routing import ForwardRule

# local
from local_lib.p4runtime_lib import SwitchConnection
from local_lib.settings import Settings
from local_lib.global_ import GlobalController

# other
from uuid import UUID
from typing import Set

class RoutingManager:

    def __init__(self,
            logger: Logger,
            settings: Settings,
            switch_connection: SwitchConnection,
            global_controller: GlobalController
        ) -> None:
        self._logger = logger
        self._settings = settings
        self._switch_connection = switch_connection
        self._global_controller = global_controller
        self._global_controller.get_service("registration").on_register(self._init_subnets)
        self._hosts = set() # type: Set[ Host ]

    def _init_subnets(self, id_: UUID) -> None:
        for subnet in self._settings.get_subnets():
            self.add_subnet(subnet)

    def _write_ipv4_rule(self, address: Address, prefix: int, mac: str, port: int) -> None:
        self._switch_connection.write(
                table_name="ingress.ethernet.ipv4.forward",
                match_fields={
                    "hdr.ipv4.dstAddr": (str(address), prefix),
                    "hdr.ethernet.dstAddr": self._settings.get_mac()
                },
                action_name="ingress.ethernet.ipv4.do_forward",
                action_params={
                    "dstAddr": mac,
                    "port": port
                }
            )

    def _delete_ipv4_rule(self, address: Address, prefix: int) -> None:
        self._switch_connection.delete(
                table_name="ingress.ethernet.ipv4.forward",
                match_fields={
                    "hdr.ipv4.dstAddr": (str(address), prefix),
                    "hdr.ethernet.dstAddr": self._settings.get_mac()
                }
            )

    def new_forward_rule(self, rule: ForwardRule) -> None:
        self._logger.info("New forward rule: " + str(rule))
        subnet = rule.get_subnet()
        self._write_ipv4_rule(subnet.network_address, subnet.prefixlen,
                rule.get_dst_mac(), rule.get_port())

    def remove_forward_rule(self, rule: ForwardRule) -> None:
        self._logger.info("Remove forward rule: " + str(rule))
        subnet = rule.get_subnet()
        self._delete_ipv4_rule(subnet.network_address, subnet.prefixlen)

    def add_host(self, host: Host) -> None:
        self._logger.info("Adding host: " + str(host))
        self._hosts.add(host)
        self._write_ipv4_rule(host.get_address(), 32, host.get_mac(), host.get_port())

    def get_hosts(self) -> Set[ Host ]:
        return self._hosts

    def add_subnet(self, subnet: Network) -> None:
        self._logger.info("Adding subnet: " + str(subnet))
        self._global_controller.get_service("routing").add_subnet(subnet)

    def remove_subnet(self, subnet: Network) -> None:
        self._logger.info("Remove subnet: " + str(subnet))
        self._global_controller.get_service("routing").remove_subnet(subnet)

    def write_default_settings(self, settings: Settings) -> None:
        self._logger.debug("Writing default routing rules.", 2)
        for host in settings.get_hosts():
            self.add_host(host)
