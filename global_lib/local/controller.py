# common
from common_lib.stub import LocalController as Base, Ipsec
from common_lib.credentials import Credentials
from common_lib.stub.command import Command

# global
from global_lib.local.lldp import LLDP
from global_lib.local.macsec import Macsec
from global_lib.local.routing import Routing
from global_lib.local.concentrator import Concentrator

class LocalController(Base):
    def add_services(self) -> None:
        super().add_services()

        self.add_service("command", Command)
        self.add_service("lldp", LLDP)
        self.add_service("macsec", Macsec)
        self.add_service("ipsec", Ipsec)
        self.add_service("routing", Routing)
        self.add_service("concentrator", Concentrator)
