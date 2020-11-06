# common
from common_lib.ipaddress import Network

# protobuf
from routing_pb2 import forward_rule # type: ignore

# other
from typing import Set
from ipaddress import ip_network
from uuid import UUID

class ForwardRule:

    def __init__(self, src: UUID, dst: UUID, dst_mac: str, port: int, subnet: Network):
        self._src = src
        self._dst = dst
        self._dst_mac = dst_mac
        self._port = port
        self._subnet = subnet

    def get_src(self) -> UUID:
        return self._src

    def get_dst(self) -> UUID:
        return self._dst

    def get_dst_mac(self) -> str:
        return self._dst_mac

    def get_port(self) -> int:
        return self._port

    def get_subnet(self) -> Network:
        return self._subnet

    def to_proto(self) -> forward_rule:
        return forward_rule(
            src = str(self.get_src()),
            dst = str(self.get_dst()),
            dst_mac = self.get_dst_mac(),
            port = self.get_port(),
            subnet = str(self.get_subnet())
        )

    @classmethod
    def from_proto(Class, proto: forward_rule):
        return Class(UUID(proto.src), UUID(proto.dst), \
                proto.dst_mac, proto.port, ip_network(proto.subnet))

    def __str__(self) -> str:
        return "ForwardRule(src=" + str(self.get_src()) + \
                ", dst=" + str(self.get_dst()) + \
                ", dst_mac=" + str(self.get_dst_mac()) + \
                ", port=" + str(self.get_port()) + \
                ", subnet=" + str(self.get_subnet()) + ")"
