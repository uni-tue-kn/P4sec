# common
from common_lib.controller import ControllerSettings, TargetSettings, SubSettings
from common_lib.ipaddress import Address, Network, Subnet, Host
from common_lib.credentials import Credentials

# other
from json import load
from ipaddress import ip_network, ip_address
from typing import Set, Dict
from os.path import join, dirname

class SwitchSettings(SubSettings):

    def __init__(self, data: Dict) -> None:
        super().__init__(data)

    def resolve(self, x):
        return join(join(dirname(__file__), "../build"), x)

    def get_p4info(self) -> str:
        return self.resolve("p4c/basic.txt")

    def get_bmv2(self) -> str:
        return self.resolve("p4c/basic.json")

    def get_device_id(self) -> str:
        return self.get_data("device_id")

    def get_address(self) -> str:
        return self.get_data("address")

    def get_num_ports(self) -> int:
        return self.get_data("num_ports")

    def get_notification_socket(self) -> str:
        return self.get_data("notification_socket")

class PortAuthorizationSettings(SubSettings):

    def __init__(self, data: Dict) -> None:
        super().__init__(data)

    def get_type(self) -> str:
        return self.get_data("type")

class RadiusAuthorizationSettings(PortAuthorizationSettings):

    def __init__(self, data: Dict) -> None:
        super().__init__(data)

    def get_ip(self) -> str:
        return self.get_data("ip")

    def get_port(self) -> int:
        return self.get_data("port")

    def get_secret(self) -> bytes:
        return self.get_data("secret").encode("ascii")

class Settings(ControllerSettings):

    def __init__(self, args):
        super().__init__(args)

    def get_ip(self) -> Address:
        return ip_address(self.get_data("ip"))

    def get_mac(self) -> str:
        return self.get_data("mac")

    def get_gateway(self) -> str:
        return self.get_data("gateway")

    def is_concentrator(self) -> bool:
        return bool(self.get_data("concentrator"))

    def get_global_controller(self) -> TargetSettings:
        return TargetSettings(self.get_data("global"))

    def get_switch(self) -> SwitchSettings:
        return SwitchSettings(self.get_data("switch"))

    def get_subnets(self) -> Set[ Network ]:
        return set([ ip_network(x) for x in self.get_data("subnets") ])

    def get_routing(self) -> Set[ Subnet ]:
        return set([ Subnet(ip_network(x["address"]), str(x["mac"]), int(x["port"]))
            for x in self.get_data("routing") ])

    def get_hosts(self) -> Set[ Host ]:
        return set([ Host(ip_address(x["address"]), str(x["mac"]), int(x["port"]))
            for x in self.get_data("hosts") ])

    def get_extern_ports(self) -> Set[ int ]:
        return set([ int(x) for x in self.get_data("extern_ports") ])

    def get_port_authorization(self) -> PortAuthorizationSettings:
        if not "port-authorization" in self._data:
            return PortAuthorizationSettings({ "type": None })
        elif self.get_data("port-authorization")["type"] == "radius":
            return RadiusAuthorizationSettings(self.get_data("port-authorization"))
        else:
            return PortAuthorizationSettings({ "type": None })

    def has_port_authorization(self) -> bool:
        return self.get_port_authorization().get_type() != None
