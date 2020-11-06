# common
from common_lib.stub import StubController
from common_lib.credentials import Credentials

# client
from client_lib.settings import Settings
from client_lib.global_.registration import Registration
from client_lib.global_.macsec import Macsec

class GlobalController(StubController):
    def __init__(self, settings: Settings, address: str, secure: bool = True):
        super().__init__("wan-controller", address, settings.get_global_credentials(), secure=secure)
        self.add_service("registration", Registration, settings)
        self.add_service("macsec", Macsec)
