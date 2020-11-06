from common_lib.exception.base import Base
from common_lib.ipaddress import Address

class UnknownEndpoint(Base):

    def __init__(self, address: Address):
        super().__init__("Unknown endpoint \"" + str(address) + "\"")
