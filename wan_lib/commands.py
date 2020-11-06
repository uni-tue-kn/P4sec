# common
from common_lib.repl import Repl
from common_lib.manager import ControllerManager
from common_lib.ipsec import Endpoint
from common_lib.stub import StubController

# wan
from wan_lib.manager import NetworkManager

# other
from re import match, search
from ipaddress import ip_address
from uuid import UUID
from typing import Tuple

class Commands(Repl):

    def __init__(self, controller):
        super().__init__(controller)
        self.intro = "Welcome to the p4sec wan controller."

    #############################################################
    # Getters                                                  #
    #############################################################

    def get_network_manager(self) -> NetworkManager:
        return self.controller.network_manager

    def get_controller_manager(self) -> ControllerManager:
        return self.controller.controller_manager

    #############################################################
    # Commands                                                 #
    #############################################################

    def do_list_controllers(self, line: str) -> None:
        self.list(self.get_controller_manager().get_controllers())

    def do_list_endpoints(self, line: str) -> None:
        self.list(self.get_network_manager().get_endpoints())

    def _get_endpoints(self, line: str) -> Tuple[ Endpoint, Endpoint ]:
        ips = match("^\\s*([^\\s]+)\\s+([^\\s]+)\\s*$", line)

        if ips is None:
            raise Exception("Please provide the IPs of the endpoints")

        ip1 = ip_address(ips.group(1))
        ip2 = ip_address(ips.group(2))

        endpoint1 = self.get_network_manager().get_endpoint(ip1)
        endpoint2 = self.get_network_manager().get_endpoint(ip2)

        return endpoint1, endpoint2

    def do_connect(self, line: str) -> None:
        endpoint1, endpoint2 = self._get_endpoints(line)
        self.get_network_manager().connect(endpoint1, endpoint2)

    def do_disconnect(self, line: str) -> None:
        endpoint1, endpoint2 = self._get_endpoints(line)
        self.get_network_manager().disconnect(endpoint1, endpoint2)


    def _get_controller(self, identification: str) -> StubController:
        if identification.startswith("#"):
            match = search("^#([^ ]+).*$", identification)
            if match is not None:
                return self.get_controller_manager().get_controller(UUID(match.group(1)))
            else:
                raise Exception("Malformatted controller id.")
        else:
            match = search("^([^ ]+).*$", identification)
            if match is not None:
                return self.get_controller_manager().get_controller_by_name(match.group(1))
            else:
                raise Exception("Malformatted controller name.")

    def do_gc(self, line):
        line = line.strip()
        match = search("^([^ ]+)(.*)$", line)
        identifier = match.group(1)

        controller = self._get_controller(identifier) \
                if identifier[0] != '#' \
                else self.get_controller_manager().get_controller(UUID(identifier[1:]))

        switch_command = match.group(2)
        result = controller.get_service("command").run_command(switch_command)
        self.print(result)
