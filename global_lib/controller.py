# common
from common_lib.controller import Controller as BaseController

# global
from global_lib.settings import Settings
from global_lib.wan import WanController
from global_lib.manager import IpsecManager, LLDPManager, MacsecManager, ControllerManager, RoutingManager
from global_lib.interface import Interface
from global_lib.commands import Commands

# other
from grpc import RpcError # type: ignore

class Controller(BaseController):
    """
    Global controller which manages all local controller.
    Every local controller connects to the global controller which
    will then generate a global topology and send instructions to the local
    controller.
    """

    def __init__(self, settings: Settings):
        super().__init__(Commands(self), settings.is_interactive())
        self.settings = settings

        # stub
        self.wan_controller = WanController(settings)

        # manager
        self.controller_manager = ControllerManager(self.logger, self.event_system)
        self.lldp_manager = LLDPManager(self.logger, self.controller_manager)
        self.macsec_manager = MacsecManager(self.logger, self.lldp_manager, self.event_system)
        self.routing_manager = RoutingManager(self.logger, self.wan_controller,
                self.controller_manager, self.lldp_manager.get_topology())
        self.ipsec_manager = IpsecManager(self.logger, self.settings, self.wan_controller,
                self.controller_manager, self.routing_manager)

        # interfaces
        self.interface = Interface(self.event_system, self.logger, \
                self.settings, self.settings.get_address(), self.repl, self.controller_manager, \
                self.lldp_manager, self.ipsec_manager, self.routing_manager, \
                self.macsec_manager, self.wan_controller)
        #self.interface2 = Interface(self.event_system, self.logger, \
        #        self.settings, "10.0.1.4:5000", self.repl, self.controller_manager, \
        #        self.lldp_manager, self.ipsec_manager, self.routing_manager, \
        #        self.macsec_manager, secure=False)

    def prepare(self):
        self.logger.info("Start global controller.")

        #self.interface2.start()
        self.interface.start()

        self.macsec_manager.start()
        self.wan_controller.get_service("registration").register()

    def shutdown(self):
        BaseController.shutdown(self)

        try:
            self.wan_controller.get_service("registration").unregister()
        except RpcError:
            self.logger.error("Could not unregister at wan controller.")
        self.macsec_manager.teardown()

        self.interface.stop()
        #self.interface2.stop()
