# common
from common_lib.stub import StubController
from common_lib.credentials import Credentials

# local
from local_lib.global_.registration import Registration
from local_lib.global_.lldp import LLDP
from local_lib.global_.routing import Routing
from local_lib.global_.macsec import Macsec
from local_lib.global_.ipsec import Ipsec

class GlobalController(StubController):
    def __init__(self, controller):
        settings = controller.settings
        gc_settings = settings.get_global_controller()
        address = gc_settings.get_address()
        credentials = gc_settings.get_credentials()
        super().__init__("global-controller", address, credentials)

        self.add_service("registration", Registration, settings)
        self.add_service("lldp", LLDP)
        self.add_service("macsec", Macsec)
        self.add_service("ipsec", Ipsec)
        self.add_service("routing", Routing, self.get_service("registration"))
