# common
from common_lib.topology import Edge

# other
from networkx import Graph, shortest_path, single_source_shortest_path # type: ignore
from time import time as now
from typing import Tuple, List, Callable, Set
from uuid import UUID

Handler = Callable[ [ Edge ], None ]

class Topology:
    """
    A representation of an arbitrary topology.
    This can either be a topology of a local or global
    controller.
    """

    def __init__(self):
         # Use a DiGraph to save connections
         # it is directed to assign in and out ports from each entity
        self._connections = Graph()

        self._new_edge_handlers = set() # type: Set[ Handler ]
        self._remove_edge_handlers = set() # type: Set[ Handler ]

    def on_new_edge(self, handler: Handler) -> None:
        self._new_edge_handlers.add(handler)

    def on_remove_edge(self, handler: Handler) -> None:
        self._remove_edge_handlers.add(handler)

    def get_controllers(self):
        return self._connections.nodes()

    def get_edge_controllers(self, edge: Edge) -> Tuple[ UUID, UUID ]:
        controller1 = edge.get_controller1()
        controller2 = edge.get_controller2()
        return controller1, controller2

    def set(self, edge: Edge) -> None:
        """ Set a connection between to switches """
        controller1, controller2 = self.get_edge_controllers(edge)

        if self.has(edge):
            self.remove(edge.get_controller1(), edge.get_controller2())

        self._connections.add_edge(controller1, controller2, edge=edge)
        self._notifiy_new_edge_handlers(edge)

    def get_edge(self, x: UUID, y: UUID) -> Edge:
        return self._connections[x][y]["edge"]

    def has(self, edge: Edge) -> bool:
        """ Check if a connection between to switches exists. """
        controller1, controller2 = self.get_edge_controllers(edge)
        return self._connections.has_edge(controller1, controller2) and \
                self._connections[controller1][controller2]["edge"] == edge

    def has_node(self, id_: UUID) -> bool:
        return self._connections.has_node(id_)

    def remove(self, controller1: UUID, controller2: UUID) -> None:
        """ Remove a connection between two switches. """
        edge = self.get_edge(controller1, controller2)
        self._connections.remove_edge(controller1, controller2)
        self._notify_remove_edge_handlers(edge)

    def refresh(self, edge: Edge) -> None:
        """ Update the time of an edge. """
        controller1, controller2 = self.get_edge_controllers(edge)
        self._connections[controller1][controller2]["edge"].refresh()

    def get_edges_older_than(self, t: int) -> List[ Edge ]:
        return [ edge[2]["edge"] for edge in self._connections.edges.data() \
                if int(now()) - edge[2]["edge"].get_last_updated() > t ]

    def get_edges_of(self, x: UUID):
        return [ edge[2]["edge"] for edge in self._connections.edges([ x ], data=True) ]

    def get_edges(self) -> List[ Edge ]:
        return [ edge[2]["edge"] for edge in self._connections.edges.data() ]

    def shortest_path(self, start: UUID, end: UUID) -> List[ UUID ]:
        return shortest_path(self._connections, start, end)

    def shortest_paths_from(self, start: UUID) -> List[ List[ UUID ] ]:
        paths = single_source_shortest_path(self._connections, start)
        return [ path for key, path in paths.items() ]

    def __str__(self) -> str:
        return "Topology(" + str(self._connections.edges()) + ")"

    def _notifiy_new_edge_handlers(self, edge: Edge) -> None:
        for handler in self._new_edge_handlers:
            handler(edge)

    def _notify_remove_edge_handlers(self, edge: Edge) -> None:
        for handler in self._remove_edge_handlers:
            handler(edge)
