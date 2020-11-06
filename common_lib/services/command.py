# common
from common_lib.services.service import Service
from common_lib.server import synchronize
from common_lib.logger import Logger
from common_lib.event import EventSystem
from common_lib.repl import Repl

# protobuf
from command_pb2_grpc import add_CommandServicer_to_server, CommandServicer # type: ignore
from text_pb2 import text # type: ignore
from grpc import ServicerContext # type: ignore

class CommandService(Service, CommandServicer):

    def __init__(self, event_system: EventSystem, logger: Logger, commands: Repl):
        Service.__init__(self, add_CommandServicer_to_server, event_system)
        self._logger = logger
        self._commands = commands

    @synchronize
    def run_command(self, request: text, context: ServicerContext) -> text:
        self._logger.info("Running command " + str(request.value))
        result = text()
        self._commands.record()
        self._commands.onecmd(request.value)
        result.value = self._commands.flush_record()
        return result
