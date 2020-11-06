# common
from common_lib.exception import NoConcentrator
from common_lib.repl import Repl
from common_lib.manager import ControllerManager
from common_lib.stub import StubController

# global
from global_lib.manager import LLDPManager, IpsecManager

# other
from tabulate import tabulate
from re import search
from text_pb2 import text # type: ignore
from uuid import UUID

class Commands(Repl):
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        self.intro = "Welcome to the global p4macsec controller!"

    #############################################################
    # Getters                                                  #
    #############################################################

    def get_controller_manager(self) -> ControllerManager:
        return self.controller.controller_manager

    def get_lldp_manager(self) -> LLDPManager:
        return self.controller.lldp_manager

    def get_ipsec_manager(self) -> IpsecManager:
        return self.controller.ipsec_manager

    #############################################################
    # Static commands                                          #
    #############################################################

    def do_print_topology(self, line):
        "show the lldp"
        edges = self.get_lldp_manager().get_topology().get_edges()

        for edge in edges:
            controller1, controller2 = self.get_lldp_manager().get_edge_controllers(edge)
            self.print("(" + controller1.get_name() + ", " + controller2.get_name() + ")")

    def do_switch_id(self, line: str):
        name = line.strip()
        try:
            controller = self.get_controller_manager().get_controller_by_name(name)
            self.print(str(controller.get_id()))
        except Exception as e:
            self.print(str(e))

    def do_list_switches(self, line):
        self.list(self.get_controller_manager().get_controllers())

    def do_list_concentrators(self, line):
        self.list(self.get_ipsec_manager().get_concentrators())

    #############################################################
    # Dynamic commands                                         #
    #############################################################

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

    def do_lc(self, line):
        line = line.strip()
        match = search("^([^ ]+)(.*)$", line)
        controller = self._get_controller(match.group(1))
        switch_command = match.group(2)
        result = controller.get_service("command").run_command(switch_command)
        self.print(result)
