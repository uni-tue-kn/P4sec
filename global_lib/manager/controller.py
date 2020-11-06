# common
from common_lib.manager import ControllerManager as Base
from common_lib.stub import LocalController
from common_lib.event import EventSystem
from common_lib.logger import Logger

# other
from typing import cast, List
from uuid import UUID

class ControllerManager(Base):

    def __init__(self, logger: Logger, event_system: EventSystem) -> None:
        super().__init__(logger, event_system)

    def get_local_controllers(self) -> List[ LocalController ]:
        return cast(List[ LocalController ], super().get_controllers())

    def get_local_controller(self, id_: UUID) -> LocalController:
        return cast(LocalController, self.get_controller(id_))

    def get_controller_by_mac(self, mac: str) -> LocalController:
        for controller in self.get_local_controllers():
            if controller.get_mac() == mac:
                return controller
        raise Exception("Unknown Controller")
