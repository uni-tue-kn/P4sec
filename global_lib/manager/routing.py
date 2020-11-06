# common
from common_lib.logger import Logger
from common_lib.ipaddress import Network
from common_lib.topology import Edge, Topology
from common_lib.routing import ForwardRule
from common_lib.stub import LocalController, StubController

# global
from global_lib.manager import ControllerManager
from global_lib.wan import WanController

# other
from typing import Set, List, Tuple, Dict
from uuid import UUID
from collections import defaultdict

class RoutingManager:

    def __init__(self,
            logger: Logger,
            wan_controller: WanController,
            controller_manager: ControllerManager,
            topology: Topology
        ) -> None:

        self._logger = logger
        self._wan_controller = wan_controller
        self._controller_manager = controller_manager
        self._topology = topology

        self._topology.on_new_edge(self._new_connection)
        self._topology.on_remove_edge(self._remove_connection)
        self._controller_manager.listen_remove_controller(self._remove_controller)

        self._controller_subnets = defaultdict(set) # type: defaultdict
        self._forward_rules = set() # type: Set[ ForwardRule ]

    def _update_routes(self) -> None:
        rules = [ ] # type: List[ ForwardRule ]
        for controller in self._controller_manager.get_local_controllers():
            for subnet in self._controller_subnets[controller.get_id()]:
                rules += self._get_forward_rules(controller, subnet)

        # remove duplicates -> use this ugly method because python sets suck!!!!!
        x = dict()
        for rule in rules:
            x[str(rule)] = rule
        rules = [ ]
        for key, rule in x.items():
            rules.append(rule)

        y = dict()
        for rule in self._forward_rules:
            y[str(rule)] = rule

        # delete old rules
        for key, rule in y.items():
            if key not in x:
                source = self._controller_manager.get_controller(rule.get_src())
                try:
                    source.get_service("routing").remove_forward_rule(rule)
                except:
                    self._logger.warn("Could not remove forwarding rule: " + str(rule))

        # write new rules
        for key, rule in x.items():
            if key not in y:
                source = self._controller_manager.get_controller(rule.get_src())
                source.get_service("routing").new_forward_rule(rule)

        self._forward_rules = set([ rule for key, rule in x.items() ])

    def _get_path_forward_rules(self,
            path: List[ UUID ],
            subnet: Network
        ) -> Set[ ForwardRule ]:
        rules = set() # type: Set[ ForwardRule ]

        for i in range(len(path) - 1):
            source_id = path[i + 1]
            target_id = path[i]
            source = self._controller_manager.get_local_controller(source_id)
            target = self._controller_manager.get_local_controller(target_id)
            edge = self._topology.get_edge(source_id, target_id)
            port = edge.get_port1() if edge.get_controller1() == source_id else edge.get_port2()
            rules.add(ForwardRule(source_id, target_id, target.get_mac(), port, subnet))

        return rules

    def _get_forward_rules(self,
            controller: LocalController,
            subnet: Network
        ) -> Set[ ForwardRule ]:
        if self._topology.has_node(controller.get_id()):
            paths = self._topology.shortest_paths_from(controller.get_id())
            edges = set() # type: Set[ ForwardRule ]
            for path in paths:
                edges = edges.union(self._get_path_forward_rules(path, subnet))
            return edges
        else:
            return set()

    def get_all_subnets(self) -> Set[ Network ]:
        return set(subnet for _id, subnets in self._controller_subnets.items()
                for subnet in subnets)

    def add_subnet_silent(self, controller_id: UUID, subnet: Network) -> None:
        self._logger.info("Add subnet: \"" + str(subnet) + "\" to " + str(controller_id))
        self._controller_subnets[controller_id].add(subnet)
        self._update_routes()

    def add_subnet(self, controller_id: UUID, subnet: Network) -> None:
        self.add_subnet_silent(controller_id, subnet)

        # notify wan controller
        self._wan_controller.get_service("routing").add_subnet(subnet)

    def remove_subnet_silent(self, controller_id: UUID, subnet: Network) -> None:
        self._logger.info("Remove subnet: \"" + str(subnet) + "\" from " + str(controller_id))
        self._controller_subnets[controller_id].remove(subnet)
        self._update_routes()

    def remove_subnet(self, controller_id: UUID, subnet: Network) -> None:
        self.remove_subnet_silent(controller_id, subnet)

        # notify wan controller
        self._wan_controller.get_service("routing").remove_subnet(subnet)

    def _new_connection(self, edge: Edge) -> None:
        self._update_routes()

    def _remove_connection(self, edge: Edge) -> None:
        self._update_routes()

    def _remove_controller(self, controller: StubController) -> None:
        self._logger.debug("handle remove controller -> delete subnets")
        to_remove = [ x for x in self._controller_subnets[controller.get_id()] ]
        for subnet in to_remove:
            self.remove_subnet(controller.get_id(), subnet)
