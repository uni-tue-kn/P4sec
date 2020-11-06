# common
from common_lib.repl import Repl
from common_lib.ipaddress import Host, Subnet

# local
from local_lib.manager import RoutingManager, PortAuthorizer, Authenticator

# other
from re import match
from ipaddress import ip_address, ip_network
from typing import Tuple

class Commands(Repl):

    def __init__(self, controller):
        super().__init__(controller)
        self.intro = "Welcome to the local p4macsec controller!"

    def get_routing_manager(self) -> RoutingManager:
        return self.controller.routing_manager

    def get_port_authorizer(self) -> PortAuthorizer:
        return self.controller.port_authorizer

    def get_authenticator(self) -> Authenticator:
        return self.controller.authenticator

    def do_list_hosts(self, line: str) -> None:
        self.list(self.get_routing_manager().get_hosts())

    def do_add_host(self, line: str) -> None:
        params = match("^\\s*([^\\s]+)\\s+([^\\s]+)\\s+([^\\s]+)\\s*$", line)
        if params is None:
            self.print("Unknown parameters.")
            return

        ip = ip_address(params.group(1))
        mac = str(params.group(2))
        port = int(params.group(3))
        host = Host(ip, mac, port)

        self.get_routing_manager().add_host(host)

    def do_add_subnet(self, line: str) -> None:
        params = match("^\\s*([^\\s]+)\\s*$", line)
        if params is None:
            self.print("Unknown parameters.")
            return

        subnet = ip_network(params.group(1))
        self.get_routing_manager().add_subnet(subnet)

    def _get_port_and_mac(self, line: str) -> Tuple[ int, str ]:
        params = match("^\\s*([0-9]+)\\s+(([0-9]{2}:?){6})\\s*$", line)

        if params is None:
            raise Exception("Unknown parameters.")

        port = int(params.group(1))
        mac = params.group(2)

        return port, mac

    def do_grant_port_access(self, line: str) -> None:
        port, mac = self._get_port_and_mac(line)
        self.get_port_authorizer().authorize(port, mac)

    def do_revoke_port_access(self, line: str) -> None:
        params = match("^\\s*(([0-9]{2}:?){6})\\s*$", line)

        if params is None:
            self.print("Unknown parameters.")
            return

        mac = params.group(1)

        port = self.get_port_authorizer().get_port_mapping()[mac]
        self.get_port_authorizer().unauthorize(port, mac)

    def do_list_port_mapping(self, line: str) -> None:
        self.list([ "mac: " + str(mac) + ", port: " + str(port) for mac, port in 
            self.get_port_authorizer().get_port_mapping().items() ])

    def do_list_supplicants(self, line: str) -> None:
        supplicants = self.get_authenticator().get_supplicant_manager().get_all()
        self.list(supplicants)

    def do_unauthorize_supplicant(self, line: str) -> None:
        port, mac = self._get_port_and_mac(line)
        supplicant = self.get_authenticator().get_supplicant_manager()[port][mac]
        self.get_port_authorizer().unauthorize(port, mac)
        supplicant.send_failure()

