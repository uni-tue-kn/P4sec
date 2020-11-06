# common
from common_lib.macsec import Channel, Address
from common_lib.topology import Edge

# proto
from macsec_pb2 import rule # type: ignore

# other
from datetime import datetime
from typing import Optional

class Rule:

    def __init__(self,
            validate: Channel,
            protect: Channel,
            soft_packet_limit: int,
            hard_packet_limit: int,
            soft_time_limit: datetime,
            hard_time_limit: datetime,
            edge: Edge,
            peer: Optional[Address] = None
        ) -> None:
        self._validate = validate
        self._protect = protect
        self._soft_packet_limit = soft_packet_limit
        self._hard_packet_limit = hard_packet_limit
        self._soft_time_limit = soft_time_limit
        self._hard_time_limit = hard_time_limit
        self._edge = edge
        self._peer = peer

    def get_validate(self) -> Channel:
        return self._validate

    def get_protect(self) -> Channel:
        return self._protect

    def get_soft_packet_limit(self) -> int:
        return self._soft_packet_limit

    def get_hard_packet_limit(self) -> int:
        return self._hard_packet_limit

    def get_soft_time_limit(self) -> datetime:
        return self._soft_time_limit

    def get_hard_time_limit(self) -> datetime:
        return self._hard_time_limit

    def get_edge(self) -> Edge:
        return self._edge

    def get_peer(self) -> Optional[Address]:
        return self._peer

    def __str__(self) -> str:
        return "Rule(" + \
                str(self.get_validate().get_address()) + ", " + \
                str(self.get_protect().get_address()) + \
                ")"

    def to_proto(self) -> rule:
        edge = self.get_edge()
        return rule(
            validate=self.get_validate().to_proto(),
            protect=self.get_protect().to_proto(),
            soft_packet_limit=self.get_soft_packet_limit(),
            hard_packet_limit=self.get_hard_packet_limit(),
            soft_time_limit=int(datetime.timestamp(self.get_soft_time_limit())),
            hard_time_limit=int(datetime.timestamp(self.get_hard_time_limit())),
            has_edge = edge is not None,
            edge = edge.to_proto() if not edge is None else None,
            has_peer = self._peer is not None,
            peer = self._peer.to_proto() if not self._peer is None else None
        )

    @staticmethod
    def from_proto(proto: rule):
        return Rule(
                Channel.from_proto(proto.validate),
                Channel.from_proto(proto.protect),
                proto.soft_packet_limit,
                proto.hard_packet_limit,
                datetime.fromtimestamp(proto.soft_time_limit),
                datetime.fromtimestamp(proto.hard_time_limit),
                Edge.from_proto(proto.edge) if proto.has_edge else None,
                Address.from_proto(proto.peer) if proto.has_peer else None
            )
