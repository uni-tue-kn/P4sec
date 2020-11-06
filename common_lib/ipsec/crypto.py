from abc import abstractmethod
from os import urandom

from ipsec_pb2 import crypto # type: ignore
from enum import Enum

class CryptoType(Enum):
    AES_CTR = "aes-ctr"
    HMAC_MD5 = "hmac-md5"

class SymmetricCryptoAlorithm:
    def __init__(self, key: bytes) -> None:
        self._key = key

    def get_key(self) -> bytes:
        return self._key

    @abstractmethod
    def get_type(self) -> CryptoType:
        raise NotImplementedError()

    def to_proto(self) -> crypto:
        return crypto(
            algorithm = self.get_type().value,
            key = self.get_key()
        )

    @staticmethod
    def from_proto(message):
        algorithm = CryptoType(message.algorithm)
        if algorithm == CryptoType.AES_CTR:
            return AES_CTR(message.key)
        elif algorithm == CryptoType.HMAC_MD5:
            return HMAC_MD5(message.key)

class AES_CTR(SymmetricCryptoAlorithm):
    def __init__(self, key=None):
        super().__init__(urandom(20) if key is None else key)

    def get_type(self) -> CryptoType:
        return CryptoType.AES_CTR

class HMAC_MD5(SymmetricCryptoAlorithm):
    def __init__(self, key=None):
        super().__init__(urandom(16) if key is None else key)

    def get_type(self) -> CryptoType:
        return CryptoType.HMAC_MD5
