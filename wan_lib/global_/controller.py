# common
from common_lib.stub import StubController, LocalController, Ipsec
from common_lib.stub.command import Command

class GlobalController(StubController):

    def add_services(self) -> None:
        super().add_services()

        self.add_service("ipsec", Ipsec)
        self.add_service("command", Command)
