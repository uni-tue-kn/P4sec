# common
from common_lib.ipsec.connection import Connection
from common_lib.ipsec.endpoint import Endpoint

# proto
from ipsec_pb2 import tunnel # type: ignore

# other
from uuid import UUID, uuid1
from datetime import timedelta

class Tunnel:

    def __init__(self,
            endpoint1: Endpoint,
            endpoint2: Endpoint,
            connection_1_to_2: Connection,
            connection_2_to_1: Connection,
            soft_time_limit: timedelta,
            hard_time_limit: timedelta,
            soft_packet_limit: int,
            hard_packet_limit: int,
            id_=None
        ):
        self._id = uuid1() if id_ is None else id_
        self._endpoint1 = endpoint1
        self._endpoint2 = endpoint2
        self._connection_1_to_2 = connection_1_to_2
        self._connection_2_to_1 = connection_2_to_1
        self._soft_time_limit = soft_time_limit
        self._hard_time_limit = hard_time_limit
        self._soft_packet_limit = soft_packet_limit
        self._hard_packet_limit = hard_packet_limit

    def get_id(self) -> UUID:
        return self._id

    def get_endpoint1(self) -> Endpoint:
        return self._endpoint1

    def get_endpoint2(self) -> Endpoint:
        return self._endpoint2

    def get_connection_1_to_2(self) -> Connection:
        return self._connection_1_to_2

    def get_connection_2_to_1(self) -> Connection:
        return self._connection_2_to_1

    def get_soft_time_limit(self) -> timedelta:
        return self._soft_time_limit

    def get_hard_time_limit(self) -> timedelta:
        return self._hard_time_limit

    def get_soft_packet_limit(self) -> int:
        return self._soft_packet_limit

    def get_hard_packet_limit(self) -> int:
        return self._hard_packet_limit

    def to_proto(self):
        return tunnel(
            id = str(self.get_id()),
            endpoint1 = self.get_endpoint1().to_proto(),
            endpoint2 = self.get_endpoint2().to_proto(),
            connection_1_to_2 = self.get_connection_1_to_2().to_proto(),
            connection_2_to_1 = self.get_connection_2_to_1().to_proto(),
            soft_time_limit = int(self.get_soft_time_limit().total_seconds()),
            hard_time_limit = int(self.get_hard_time_limit().total_seconds()),
            soft_packet_limit = self.get_soft_packet_limit(),
            hard_packet_limit = self.get_hard_packet_limit()
        )

    @classmethod
    def from_proto(Class, message):
        endpoint1 = Endpoint.from_proto(message.endpoint1)
        endpoint2 = Endpoint.from_proto(message.endpoint2)
        connection_1_to_2 = Connection.from_proto(message.connection_1_to_2)
        connection_2_to_1 = Connection.from_proto(message.connection_2_to_1)
        soft_time_limit = timedelta(seconds=message.soft_time_limit)
        hard_time_limit = timedelta(seconds=message.hard_time_limit)
        soft_packet_limit = message.soft_packet_limit
        hard_packet_limit = message.hard_packet_limit
        return Class(endpoint1, endpoint2, connection_1_to_2, connection_2_to_1, \
                soft_time_limit, hard_time_limit, soft_packet_limit,
                hard_packet_limit, id_=UUID(message.id))

    def __str__(self) -> str:
        return "Tunnel(id=" + str(self.get_id()) + \
                ", endpoint1=" + str(self.get_endpoint1()) + \
                ", endpoint2=" + str(self.get_endpoint2()) + \
                ", connection1=" + str(self.get_connection_1_to_2()) + \
                ", connection2=" + str(self.get_connection_2_to_1()) + \
                ")"

    def __hash__(self) -> int:
        return int(self.get_id())

    def __eq__(self, other) -> bool:
        return self.get_id() == other.get_id()

    def __lt__(self, other) -> bool:
        return int(self.get_id()) < int(other.get_id())
