# other
from time import time as now
from topology_pb2 import edge # type: ignore
from uuid import UUID

class Edge:
    """ A connection between two network entities (switches) """

    def __init__(self, \
            controller1_id: UUID, \
            port1: int, \
            controller2_id: UUID, \
            port2: int, \
            type_="direct", \
            time=None
        ):
        self._controller1  = controller1_id
        self._port1        = port1
        self._controller2  = controller2_id
        self._port2        = port2
        self._type         = type_
        self._last_updated = int(now()) if time == None else time

    def refresh(self) -> None:
        self._last_updated = int(now())

    def get_controller1(self) -> UUID:
        return self._controller1

    def get_port1(self) -> int:
        return self._port1

    def get_controller2(self) -> UUID:
        return self._controller2

    def get_port2(self) -> int:
        return self._port2

    def get_type(self) -> str:
        return self._type

    def get_last_updated(self) -> int:
        return self._last_updated

    def __eq__(self, other) -> bool:
        c1 = self.get_controller1()
        p1 = self.get_port1()
        c2 = self.get_controller2()
        p2 = self.get_port2()

        c1_ = other.get_controller1()
        p1_ = other.get_port1()
        c2_ = other.get_controller2()
        p2_ = other.get_port2()

        return ((c1 == c1_ and p1 == p1_) or (c1 == c2_ and p1 == p2_)) and \
                ((c2 == c2_ and p2 == p2_) or (c2 == c1_ and p2 == p1_)) and \
                self.get_type() == other.get_type()

    def __str__(self) -> str:
        return "(" + str(self.get_controller1()) + ", " + str(self.get_port1()) + ") -- (" + \
                str(self.get_controller2()) + ", " + str(self.get_port2()) + ")"

    def to_proto(self) -> edge:
        return edge(
            controller1 = str(self.get_controller1()),
            port1 = self.get_port1(),
            controller2 = str(self.get_controller2()),
            port2 = self.get_port2(),
            type = self.get_type(),
            last_updated = int(self.get_last_updated())
        )

    @classmethod
    def from_proto(Class, proto: edge):
        controller1 = UUID(proto.controller1)
        port1 = proto.port1
        controller2 = UUID(proto.controller2)
        port2 = proto.port2
        type_ = proto.type
        last_updated = proto.last_updated

        return Class(controller1, port1, controller2, port2, type_, last_updated)
