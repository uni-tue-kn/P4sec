from macsec_pb2 import address # type: ignore

class Address:

    def __init__(self, mac: str, port: int):
        self._mac = mac
        self._port = port

    def get_mac(self) -> str:
        return self._mac

    def get_port(self) -> int:
        return self._port

    def __str__(self) -> str:
        return "Address(" + self.get_mac() + ", " + str(self.get_port()) + ")"

    def to_proto(self) -> address:
        proto = address()
        proto.mac = self.get_mac()
        proto.port = self.get_port()
        return proto

    @staticmethod
    def from_proto(proto):
        return Address(proto.mac, proto.port)

    def __hash__(self) -> int:
        return hash((self.get_mac(), self.get_port()))
