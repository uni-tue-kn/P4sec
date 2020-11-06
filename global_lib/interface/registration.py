# common
from common_lib.logger import Logger
from common_lib.event import EventSystem
from common_lib.services import RegistrationService as BaseService
from common_lib.manager import ControllerManager
from common_lib.server import synchronize, traceback, lazy

# global
from global_lib.local import LocalController

# grpc / protobuf
from controller_pb2 import local_controller, registration # type: ignore
from nothing_pb2 import nothing # type: ignore
from grpc import ServicerContext # type: ignore

# other
from os import urandom
from uuid import UUID

class RegistrationService(BaseService):

    def __init__(self, \
            event_system: EventSystem, \
            logger: Logger, \
            controller_manager: ControllerManager \
        ):
        super().__init__(event_system)
        self._logger = logger
        self._controller_manager = controller_manager
        self._key_bddp = urandom(32)

    @traceback("_logger")
    @synchronize
    def register_local_controller(self, \
            request: local_controller, context: ServicerContext) -> None:
        controller = LocalController.from_proto(request)
        self._controller_manager.add_controller(controller)

        response = registration()
        response.id = str(controller.get_id())
        response.key = self._key_bddp

        return response

    @traceback("_logger")
    @synchronize
    def unregister(self, request: registration, context: ServicerContext) -> nothing:
        self._controller_manager.remove_controller(UUID(request.id))
        return nothing()
