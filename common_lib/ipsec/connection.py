from common_lib.ipsec.crypto import SymmetricCryptoAlorithm
from common_lib.ipsec.endpoint import Endpoint

from ipsec_pb2 import connection # type: ignore

from os import urandom

class Connection:

    def __init__(self, \
            spi, \
            encryption: SymmetricCryptoAlorithm, \
            authentication: SymmetricCryptoAlorithm
        ):
        self._spi = spi
        self._encryption = encryption
        self._authentication = authentication

    def get_spi(self) -> bytes:
        return self._spi

    def get_encryption(self) -> SymmetricCryptoAlorithm:
        return self._encryption

    def get_authentication(self) -> SymmetricCryptoAlorithm:
        return self._authentication

    def to_proto(self) -> connection:
        return connection(
            spi = self.get_spi(),
            encryption = self.get_encryption().to_proto(),
            authentication = self.get_authentication().to_proto()
        )

    @classmethod
    def from_proto(Class, message: connection):
        encryption = SymmetricCryptoAlorithm.from_proto(message.encryption)
        authentication = SymmetricCryptoAlorithm.from_proto(message.authentication)

        return Class(message.spi, encryption, authentication)

    def __str__(self) -> str:
        return "Connection(spi=" + str(self.get_spi().hex()) + ")"
