# common
from common_lib.controller import Controller as BaseController

# local
from local_lib.settings import Settings
from local_lib.commands import Commands
from local_lib.global_ import GlobalController
from local_lib.interface import Interface

from local_lib.packet import PacketProcessor
from local_lib.manager import TopologyManager, L2Manager, IpsecManager, \
        MacsecManager, IpsecManager, RoutingManager, PortAuthorizer, Authenticator

from local_lib.p4runtime_lib import SwitchConnection, PortMonitor

# other
from os.path import join, dirname
from grpc import RpcError # type: ignore

class Controller(BaseController):
    """
    This is the distributed controller which makes connections to the global controller.
    It is a class which represents the controller.
    """

    def __init__(self, settings: Settings):
        super().__init__(Commands(self), settings.is_interactive())
        self.settings = settings

        self.global_controller = GlobalController(self)

        self.switch_connection = SwitchConnection(self.logger, self.settings)
        self.port_monitor = PortMonitor(self.logger, self.event_system, \
                self.settings.get_switch())

        self.port_authorizer = PortAuthorizer(self.logger, self.settings,
                self.event_system, self.switch_connection)
        self.authenticator = Authenticator(self.logger, self.settings, self.switch_connection,
                self.port_authorizer)
        self.routing_manager = RoutingManager(self.logger, self.settings,
                self.switch_connection, self.global_controller)
        self.ipsec_manager = IpsecManager(
                self.logger,
                settings,
                self.switch_connection,
                self.global_controller
            )
        self.topology_manager = TopologyManager(self)
        self.macsec_manager = MacsecManager(self.logger, self.settings, self.switch_connection,
                self.port_authorizer, self.global_controller, self.event_system,
                self.topology_manager)
        self.l2_manager = L2Manager(self.logger, self.settings,
                self.event_system, self.switch_connection)

        self.packet_processor = PacketProcessor(
            self.logger,
            self.topology_manager,
            self.l2_manager,
            self.authenticator,
            self.macsec_manager,
            self.ipsec_manager
        )

        self.interface = Interface(self.event_system, self.logger, self.settings,
                self.ipsec_manager, self.topology_manager, self.macsec_manager,
                self.routing_manager, self.repl)


    def prepare(self):
        # Connection to switch must be established first
        self.switch_connection.connect()

        self.port_authorizer.initialize()

        # Register at global controller
        self.interface.start()
        self.global_controller.get_service("registration").register()

        # Topology manager must be started after the connection
        # to global controller is established, because it
        # will notify the global controller on a topology update
        self.topology_manager.start()
        self.packet_processor.listen(self.switch_connection)
        self.port_monitor.start()
        self.routing_manager.write_default_settings(self.settings)


    def shutdown(self):
        self.port_monitor.stop()
        try:
            self.global_controller.get_service("registration").unregister()
        except RpcError:
            self.logger.error("Could not unregister at global controller.")
        self.interface.stop()
        self.topology_manager.teardown()
        self.port_authorizer.cleanup()
        self.switch_connection.disconnect()
