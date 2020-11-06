# common
from common_lib.topology import Topology, Edge
from common_lib.stub import StubController
from common_lib.logger import Logger
from common_lib.event import EventSystem
from common_lib.exception import AmbiguasControllerName, UnknownControllerName
from common_lib.manager import ControllerManager

# global
from global_lib.local import LocalController

# other
from typing import Callable, Tuple, List, Dict, Set
from uuid import UUID
from grpc import RpcError # type: ignore

Handler = Callable[ [ Edge ], None ]

class LLDPManager:
    """
    The lldp manager is a representation of the topology.
    If a new switch / host is registered it is added to
    the topology.
    """

    def __init__(self, \
            logger: Logger, \
            controller_manager: ControllerManager \
        ):
        self._logger = logger
        self._controller_manager = controller_manager
        self._topology = Topology()
        self._add_connection_handlers = set() # type: Set[ Handler ]
        self._remove_connection_handlers = set() # type: Set[ Handler ]

        self._controller_manager.listen_remove_controller(self._handle_controller_remove)

    #############################################################
    # Listeners                                                #
    #############################################################

    def register_add_connection(self, handler: Handler) -> None:
        self._add_connection_handlers.add(handler)

    def unregister_add_connection(self, handler: Handler) -> None:
        self._add_connection_handlers.remove(handler)

    def register_remove_connection(self, handler: Handler) -> None:
        self._remove_connection_handlers.add(handler)

    def unregister_remove_connection(self, handler: Handler) -> None:
        self._remove_connection_handlers.remove(handler)

    #############################################################
    # General functions                                        #
    #############################################################

    def get_topology(self) -> Topology:
        return self._topology

    def get_controllers(self) -> List[ LocalController ]:
        return self._controller_manager.get_local_controllers()

    def get_controller_by_mac(self, mac: str) -> StubController:
        return self._controller_manager.get_controller_by_mac(mac)

    def get_edge_controllers(self, edge: Edge) -> Tuple[ StubController, StubController ]:
        controller1 = self._controller_manager.get_controller(edge.get_controller1())
        controller2 = self._controller_manager.get_controller(edge.get_controller2())
        return controller1, controller2

    def add_silent(self, edge: Edge) -> None:
        """ Add a connection. """

        if self._topology.has(edge):
            self._logger.warn("Tried to update topology, which is already updated: " + \
                    str(edge))
            # force reset
        else:
            self._logger.info("Topology update, new connection: " + str(edge))

        self._topology.set(edge)

    def add(self, edge: Edge) -> None:
        self.add_silent(edge)

        # topology
        controller1, controller2 = self.get_edge_controllers(edge)

        controller1.get_service("lldp").add_edge(edge)
        controller2.get_service("lldp").add_edge(edge)

        self._notify_add_connection_handlers(edge)

    def remove(self, edge: Edge) -> None:
        self._logger.info("Topology update, remove connection: " + str(edge))

        self._remove_edge_from(edge.get_controller1(), edge)
        self._remove_edge_from(edge.get_controller2(), edge)
        self._topology.remove(edge.get_controller1(), edge.get_controller2())
        self._notify_remove_connection_handlers(edge)

    #############################################################
    # Private functions                                        #
    #############################################################

    def _notify_add_connection_handlers(self, edge: Edge):
        for handler in self._add_connection_handlers:
            try:
                handler(edge)
            except Exception as e:
                self._logger.error(e)

    def _notify_remove_connection_handlers(self, edge: Edge) -> None:
        for handler in self._remove_connection_handlers:
            try:
                handler(edge)
            except Exception as e:
                self._logger.error(e)

    def _remove_edge_from(self, controller_id: UUID, edge: Edge) -> None:
        try:
            controller = self._controller_manager.get_controller(controller_id)
            controller.get_service("lldp").remove_edge(edge)
        except RpcError:
            self._logger.warn("Could not reach " + str(controller_id))

    def _handle_controller_remove(self, controller: StubController) -> None:
        for edge in self.get_topology().get_edges_of(controller.get_id()):
            self.remove(edge)
