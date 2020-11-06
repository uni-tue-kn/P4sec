# common
from common_lib.ipaddress import Address, Network

# protobuf
from ipsec_pb2 import endpoint # type: ignore

# other
from typing import Union, List, Set
from ipaddress import ip_address, ip_network
from uuid import UUID

class Endpoint:
    def __init__(self,
            address: Address,
            network_id: UUID,
            is_client: bool,
            subnets: Set[ Network ] = None
        ):
        self._address = address
        self._network_id = network_id
        self._is_client = is_client
        self._subnets = set([ ]) if subnets is None else subnets # type: Set[ Network ]

    def add_subnet(self, subnet: Network) -> None:
        self._subnets.add(subnet)

    def remove_subnet(self, subnet: Network) -> None:
        self._subnets.remove(subnet)

    def get_address(self) -> Address:
        return self._address

    def get_id(self) -> UUID:
        return self._network_id

    def is_client(self) -> bool:
        return self._is_client

    def get_subnets(self) -> Set[ Network ]:
        return self._subnets

    def __eq__(self, other) -> bool:
        return self.get_id() == other.get_id()

    def __lt__(self, other) -> bool:
        return self.get_id() < other.get_id()

    def __str__(self) -> str:
        return "Endpoint(" + \
                str(self.get_address()) + \
                ", id=" + str(self.get_id()) + \
                ", is_client=" + str(self.is_client()) + \
                ", subnets={" + ", ".join([str(x) for x in self.get_subnets() ]) + "}" + \
            ")"

    def __hash__(self) -> int:
        return int(self.get_id())

    def to_proto(self) -> endpoint:
        return endpoint(
            address = self.get_address().packed,
            network_id = str(self.get_id()),
            is_client = self.is_client(),
            subnets = [ str(x) for x in self.get_subnets() ]
        )

    @staticmethod
    def from_proto(proto: endpoint):
        return Endpoint( \
                ip_address(proto.address), \
                UUID(proto.network_id), \
                proto.is_client, \
                set([ ip_network(x) for x in proto.subnets ]) \
            )
