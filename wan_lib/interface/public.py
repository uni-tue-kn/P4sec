# common
from common_lib.server import Server
from common_lib.credentials import Credentials
from common_lib.event import EventSystem
from common_lib.logger import Logger
from common_lib.manager import ControllerManager
from common_lib.ipaddress import Address

# wan
from wan_lib.settings import Settings
from wan_lib.interface.network import NetworkService
from wan_lib.interface.registration import RegistrationService
from wan_lib.interface.routing import RoutingService
from wan_lib.interface.async_ipsec import AsyncIpsecService
from wan_lib.manager import NetworkManager

class PublicInterface(Server):

    def __init__(self, \
            event_system: EventSystem, \
            logger: Logger, \
            settings: Settings, \
            controller_manager: ControllerManager, \
            network_manager: NetworkManager \
        ) -> None:

        super().__init__(logger, event_system, settings)
        self._wan_settings = settings

        self.register(RegistrationService(event_system, logger, controller_manager))
        self.register(NetworkService(event_system, logger, network_manager))
        self.register(RoutingService(event_system, logger, network_manager))
        self.register(AsyncIpsecService(event_system, logger, network_manager))

    def get_address(self) -> str:
        return self._wan_settings.get_public().get_address()

    def get_credentials(self) -> Credentials:
        return self._wan_settings.get_public().get_credentials()
