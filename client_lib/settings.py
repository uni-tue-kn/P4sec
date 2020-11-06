# common
from common_lib.controller import Settings as Base, TargetSettings
from common_lib.credentials import Credentials
from common_lib.ipaddress import Address

# other
from socket import gethostname
from ipaddress import ip_address
from netifaces import ifaddresses, AF_INET, gateways # type: ignore
from uuid import getnode as get_mac

class Settings(Base):
    def __init__(self, args) -> None:
        super().__init__(args)

    def get_interface(self) -> str:
        return str(self.get_data("interface")) if self.has("interface") \
            else gateways()["default"][AF_INET][1]

    def get_wan(self) -> TargetSettings:
        return TargetSettings(self.get_data("wan"))

    def get_name(self) -> str:
        return self.get_data("name")

    def get_ip(self) -> Address:
        interface = gateways()["default"][AF_INET][1]
        return ip_address(self.get_data("ip") if self.has("ip")
                else ifaddresses(interface)[AF_INET][0]["addr"])

    def get_mac(self) -> str:
        try:
            return open("/sys/class/net/{}/address".format(self.get_interface())).readline()[:-1]
        except:
            raise Exception("Cannot get mac address.")

    def is_concentrator(self) -> bool:
        return False

    def get_address(self) -> str:
        return "{ip}:{port}".format(ip=self.get_ip(), port=3000)

    def get_wpa_config(self) -> str:
        return self.get_data("wpa_config")

    def is_extern(self) -> bool:
        return self.get_data("extern")

    def get_credentials(self) -> Credentials:
        return self.get_global_credentials()

    def get_global_address(self) -> str:
        return self.get_data("global")["address"]

    def get_global_credentials(self) -> Credentials:
        return Credentials.read_from(self.get_data("global")["credentials"])

