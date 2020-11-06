# common
from common_lib.server import Server
from common_lib.credentials import Credentials
from common_lib.event import EventSystem
from common_lib.logger import Logger
from common_lib.services import GeneralService
from common_lib.services import CommandService
from common_lib.repl import Repl
from common_lib.manager import ControllerManager

# global
from global_lib.settings import Settings
from global_lib.manager import LLDPManager, IpsecManager, RoutingManager, MacsecManager
from global_lib.interface.registration import RegistrationService
from global_lib.interface.lldp import LLDPService
from global_lib.interface.ipsec import IpsecService
from global_lib.interface.routing import RoutingService
from global_lib.interface.macsec import MacsecService
from global_lib.wan import WanController

class Interface(Server):

    def __init__(self,
            event_system: EventSystem,
            logger: Logger,
            settings: Settings,
            address: str,
            repl: Repl,
            controller_manager: ControllerManager,
            lldp_manager: LLDPManager,
            ipsec_manager: IpsecManager,
            routing_manager: RoutingManager,
            macsec_manager: MacsecManager,
            wan_controller: WanController,
            secure: bool = True
        ):
        super().__init__(logger, event_system, settings, secure)
        self._address = address

        #############################################################
        # Services                                                 #
        #############################################################
        self.register(CommandService(event_system, logger, repl))
        self.register(RegistrationService(event_system, logger, controller_manager))
        self.register(LLDPService(event_system, logger, lldp_manager))
        self.register(IpsecService(event_system, logger, ipsec_manager, wan_controller))
        self.register(RoutingService(event_system, logger, routing_manager))
        self.register(MacsecService(event_system, logger, macsec_manager))

    def get_address(self) -> str:
        return self._address
