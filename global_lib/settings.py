# common
from common_lib.controller import ControllerSettings, TargetSettings
from common_lib.credentials import Credentials
from common_lib.ipaddress import Address

# other
from json import load
from os.path import join, dirname
from typing import Dict
from ipaddress import ip_address

class Settings(ControllerSettings):

    def __init__(self, args) -> None:
        super().__init__(args)

    def get_wan(self) -> TargetSettings:
        return TargetSettings(self.get_data("wan"))

    def get_site_address(self) -> Address:
        return ip_address(self.get_data("site-address"))
