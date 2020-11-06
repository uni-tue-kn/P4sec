# common
from common_lib.stub import StubController
from common_lib.logger import Logger
from common_lib.event import EventSystem
from common_lib.exception import AmbiguasControllerName, UnknownControllerName

# other
from typing import Tuple, List, Dict, Set, Callable
from uuid import UUID
from grpc import RpcError # type: ignore

Handler = Callable[ [ StubController ], None ]

class ControllerManager:
    """
    The topology manager is a representation of the topology.
    If a new switch / host is registered it is added to
    the topology.
    """

    def __init__(self, logger: Logger, event_system: EventSystem):
        # utils
        self._logger = logger
        self._event_system = event_system

        # attributes
        self._controllers = { } # type: Dict[UUID, StubController]

        self._event_system.set_interval(self._check_controllers, 20)#s

        self._controller_added_handlers = set() # type: Set[ Handler ]
        self._controller_removed_handlers = set() # type: Set[ Handler ]

    #############################################################
    # handlers                                                 #
    #############################################################

    def listen_new_controller(self, handler: Handler) -> None:
        self._controller_added_handlers.add(handler)

    def unlisten_new_controller(self, handler: Handler) -> None:
        self._controller_added_handlers.remove(handler)

    def listen_remove_controller(self, handler: Handler) -> None:
        self._controller_removed_handlers.add(handler)

    def unlisten_remove_controller(self, handler: Handler) -> None:
        self._controller_removed_handlers.remove(handler)

    #############################################################
    # General functions                                        #
    #############################################################

    def get_controller(self, id_: UUID) -> StubController:
        return self._controllers[id_]

    def get_controllers(self) -> List[ StubController ]:
        return [ controller for _id, controller in self._controllers.items() ]

    def get_controller_by_name(self, name: str) -> StubController:
        controllers = [ controller for controller in self.get_controllers()
                if controller.get_name() == name ]

        if len(controllers) == 0:
            raise UnknownControllerName(name)
        elif len(controllers) > 1:
            raise AmbiguasControllerName(name, controllers)

        return controllers[0]

    def add_controller(self, controller: StubController) -> None:
        self._logger.info("Registered new local controller " + controller.get_name())
        self._controllers[controller.get_id()] = controller
        self._notify_controller_added_handlers(controller)

    def remove_controller(self, id_: UUID) -> None:
        self._logger.info("Unregistered controller " + str(id_))
        self._notify_controller_removed_handlers(self.get_controller(id_))
        del self._controllers[id_]

    #############################################################
    # Private functions                                        #
    #############################################################

    def _check_controllers(self) -> None:
        self._logger.debug("Check controllers", 3)
        controllers = [ controller for controller in self.get_controllers()
                if not controller.is_client() ]
        unconnected_controllers = [ controller for controller in controllers
            if not controller.get_service("general").is_connected() ]

        for controller in unconnected_controllers:
            self._logger.info("Lost connection to " + str(controller))
            self.remove_controller(controller.get_id())

    def _notify_controller_added_handlers(self, controller: StubController) -> None:
        if controller.is_client():
            return

        for handler in self._controller_added_handlers:
            handler(controller)

    def _notify_controller_removed_handlers(self, controller: StubController) -> None:
        if controller.is_client():
            return

        for handler in self._controller_removed_handlers:
            handler(controller)
