# common
from common_lib.credentials import Credentials
from common_lib.stub import Registration, StubController, Network

# global
from global_lib.settings import Settings
from global_lib.wan.routing import Routing
from global_lib.wan.ipsec import Ipsec

class WanController(StubController):
    def __init__(self, settings: Settings):
        wan = settings.get_wan()
        super().__init__(wan.get_name(), wan.get_address(), wan.get_credentials())

        self.add_service("registration", Registration, settings.get_name(), settings.get_address(), settings.get_credentials())
        self.add_service("network", Network)
        self.add_service("routing", Routing, self.get_service("registration"))
        self.add_service("ipsec", Ipsec)
