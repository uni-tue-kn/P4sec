# common
from common_lib.logger import Logger
from common_lib.event import EventSystem
from common_lib.services import RegistrationService as BaseService
from common_lib.manager import ControllerManager
from common_lib.server import synchronize, traceback

# wan
from wan_lib.global_ import GlobalController

# grpc / protobuf
from controller_pb2 import controller, registration # type: ignore
from nothing_pb2 import nothing # type: ignore
from grpc import ServicerContext # type: ignore

# other
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

    @traceback("_logger")
    @synchronize
    def register(self, request: controller, context: ServicerContext) -> None:
        controller = GlobalController.from_proto(request)
        self._controller_manager.add_controller(controller)

        response = registration()
        response.id = str(controller.get_id())

        return response

    @traceback("_logger")
    @synchronize
    def unregister(self, request: registration, context: ServicerContext) -> nothing:
        self._controller_manager.remove_controller(UUID(request.id))
        return nothing()
