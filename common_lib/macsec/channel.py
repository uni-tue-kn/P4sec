# common
from common_lib.macsec.address import Address

# proto
from macsec_pb2 import channel # type: ignore

class Channel:

    def __init__(self, key: bytes, address: Address):
        self._key = key
        self._address = address

    def get_key(self) -> bytes:
        return self._key

    def get_address(self) -> Address:
        return self._address

    def to_proto(self) -> channel:
        return channel(
            key=self.get_key(),
            target=self.get_address().to_proto()
        )

    @staticmethod
    def from_proto(proto: channel):
        return Channel(proto.key, Address.from_proto(proto.target))
