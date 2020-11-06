# common
from common_lib.server import Server
from common_lib.credentials import Credentials
from common_lib.event import EventSystem
from common_lib.logger import Logger
from common_lib.services import CommandService
from common_lib.repl import Repl

# local
from local_lib.interface.lldp import LLDPService
from local_lib.interface.macsec import MacsecService
from local_lib.interface.ipsec import IpsecService
from local_lib.interface.routing import RoutingService
from local_lib.interface.concentrator import ConcentratorService
from local_lib.manager import IpsecManager, TopologyManager, MacsecManager, RoutingManager
from local_lib.settings import Settings

class Interface(Server):
    """ Server that lists all services of the local controller. """

    def __init__(self,
            event_system: EventSystem,
            logger: Logger,
            settings: Settings,
            ipsec_manager: IpsecManager,
            topology_manager: TopologyManager,
            macsec_manager: MacsecManager,
            routing_manager: RoutingManager,
            repl: Repl
        ):

        super().__init__(logger, event_system, settings)

        # services
        self.register(CommandService(event_system, logger, repl))
        self.register(RoutingService(event_system, logger, routing_manager))
        self.register(LLDPService(event_system, logger, topology_manager))
        self.register(MacsecService(event_system, logger, macsec_manager))
        self.register(IpsecService(event_system, logger, ipsec_manager))
        self.register(ConcentratorService(event_system, logger, ipsec_manager))
