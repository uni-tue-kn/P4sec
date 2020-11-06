# common
from common_lib.logger import Logger
from common_lib.controller import Controller
from common_lib.repl import Repl

# client
from client_lib.settings import Settings
from client_lib.wan import WanController
from client_lib.global_ import GlobalController
from client_lib.manager import TunnelManager, IpsecManager, MacsecManager, Authenticator
from client_lib.dns_interceptor import DNSInterceptor

# other
from signal import pause
from grpc import RpcError # type: ignore

class Client(Controller):
    """
    The client is executed at the user side.
    It connects the user with a given VPN network.
    """

    def __init__(self, settings: Settings):
        super().__init__(Repl(self), settings.is_interactive())
        self.settings = settings

        self.wan_controller = WanController(settings)
        self.global_controller = GlobalController(settings, settings.get_global_address(),
                secure=True)

        self.authenticator = Authenticator(self.logger, self.settings)
        self.ipsec_manager = IpsecManager(self.logger, self.settings, self.wan_controller)
        self.macsec_manager = MacsecManager(self.logger, self.settings, self.wan_controller,
                self.global_controller)
        self.dns_interceptor = DNSInterceptor(self.logger, self.settings, self.event_system)
        self.tunnel_manager = TunnelManager(self.logger, self.event_system,
                self.settings, self.wan_controller,
                self.ipsec_manager, self.dns_interceptor)

    def prepare(self):
        """ Run the client with the given settings. """
        # Test connection to server

        #self.wan_controller.get_service("registration").register()

        self.logger.info("Starting client")

        if self.settings.is_extern():
            self.dns_interceptor.start_sniffing()
            self.tunnel_manager.connect()
        else:
            self.authenticator.start()
            self.global_controller.get_service("registration").register()
            self.macsec_manager.start()


    def shutdown(self):
        """ Cleanup hook """

        #try:
        #    self.wan_controller.get_service("registration").unregister()
        #except RpcError:
        #    self.logger.error("Could not unregister at wan controller.")

        self.logger.info("Stopping client")

        if self.settings.is_extern():
            self.tunnel_manager.disconnect()
            self.dns_interceptor.stop_sniffing()
        else:
            self.authenticator.stop()
            self.macsec_manager.stop()
