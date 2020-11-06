# common
from common_lib.controller import ControllerSettings, TargetSettings
from common_lib.credentials import Credentials
from common_lib.ipaddress import Address

# other
from json import load

class Settings(ControllerSettings):
    def __init__(self, args) -> None:
        super().__init__(args)

    def get_public(self) -> TargetSettings:
        return TargetSettings(self.get_data("public"))

    def get_private(self) -> TargetSettings:
        return TargetSettings(self.get_data("private"))
