# common
from common_lib.controller import Controller as BaseController
from common_lib.manager import ControllerManager

# wan
from wan_lib.settings import Settings
from wan_lib.commands import Commands
from wan_lib.manager import NetworkManager
from wan_lib.interface import PrivateInterface, PublicInterface

class Controller(BaseController):
    def __init__(self, settings: Settings):
        super().__init__(Commands(self), settings.is_interactive())
        self.settings = settings

        self.controller_manager = ControllerManager(self.logger, self.event_system)
        self.network_manager = NetworkManager(self.logger, self.event_system, \
                self.controller_manager)

        self.private_interface = PrivateInterface(self.event_system, self.logger, settings, \
                self.controller_manager, self.network_manager)
        self.public_interface = PublicInterface(self.event_system, self.logger, settings, \
                self.controller_manager, self.network_manager)

    def prepare(self):
        self.logger.info("Start WAN controller.")
        self.private_interface.start()
        self.public_interface.start()

    def shutdown(self):
        self.logger.info("Stopping WAN controller.")
        self.private_interface.stop()
        self.public_interface.stop()
