from common_lib.ipaddress.network import Network

class Subnet:

    def __init__(self, address: Network, mac: str, port: int):
        self._address = address
        self._mac = mac
        self._port = port

    def get_address(self) -> Network:
        return self._address

    def get_mac(self) -> str:
        return self._mac

    def get_port(self) -> int:
        return self._port

    def __str__(self) -> str:
        return "Network(" + \
                "address=" + str(self.get_address()) + \
                ", mac=" + str(self.get_mac()) + \
                ", port=" + str(self.get_port()) + \
                ")"

    def __hash__(self) -> int:
        return self.get_address().__hash__()
