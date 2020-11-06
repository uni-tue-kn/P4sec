# common
from common_lib.routing import ForwardRule

# protobuf / grpc
from routing_pb2_grpc import LocalRoutingStub # type: ignore
from grpc import Channel # type: ignore

class Routing:

    def __init__(self, channel: Channel):
        self._stub = LocalRoutingStub(channel)

    def new_forward_rule(self, rule: ForwardRule) -> None:
        self._stub.new_forward_rule(rule.to_proto())

    def remove_forward_rule(self, rule: ForwardRule) -> None:
        self._stub.remove_forward_rule(rule.to_proto())
