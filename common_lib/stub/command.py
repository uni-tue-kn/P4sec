# protobuf / grpc
from command_pb2_grpc import CommandStub # type: ignore
from text_pb2 import text # type: ignore
from grpc import Channel # type: ignore

class Command:

    def __init__(self, channel: Channel):
        self._stub = CommandStub(channel)

    def run_command(self, command: str) -> str:
        request = text()
        request.value = command

        result = self._stub.run_command(request)

        return result.value
