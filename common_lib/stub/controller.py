# common
from common_lib.credentials import Credentials
from common_lib.services.service import Service
from common_lib.stub import General
from common_lib.ipaddress import Address

# protobuf / grpc
from grpc import secure_channel, insecure_channel # type: ignore
from controller_pb2 import controller, local_controller # type: ignore

# other
from uuid import uuid1, UUID
from abc import abstractmethod
from grpc import Channel
from typing import Dict, Type, Union, List
from ipaddress import ip_address, ip_network

class StubController:
    def __init__(self,
            name: str,
            address: str,
            credentials: Credentials,
            secure: bool = True,
            is_client: bool = False
        ):
        self._id = uuid1()
        self._address = address
        self._name = name
        self._credentials = credentials
        self._services = dict() # type: Dict[ str, Dict ]
        self._is_client = is_client
        self._secure = secure

        if self._secure:
            self._channel = secure_channel(self.get_address(), \
                    self._credentials.get_client_credentials())
        else:
            self._channel = insecure_channel(self.get_address())

        self.add_service("general", General)
        self.add_services()

    def unconnect(self) -> None:
        self._channel.close()

    def reconnect(self) -> None:
        if self._secure:
            self._channel = secure_channel(self.get_address(), \
                    self._credentials.get_client_credentials())
        else:
            self._channel = insecure_channel(self.get_address())

        for name, service in self._services.items():
            self._services[name]["service"] = service["Class"](self._channel,
                    *service["args"], **service["kwargs"])

    def add_service(self, name: str, NewService: Type, *args, **kwargs) -> None:
        self._services[name] = {
            "service": NewService(self._channel, *args, **kwargs),
            "Class": NewService,
            "args": args,
            "kwargs": kwargs
        }


    def add_services(self) -> None:
        """ Hook for adding services. """
        pass

    def get_service(self, name: str):
        return self._services[name]["service"]

    def get_id(self) -> UUID:
        return self._id

    def get_address(self) -> str:
        return self._address

    def get_name(self) -> str:
        return self._name

    def get_credentials(self) -> Credentials:
        return self._credentials

    def is_client(self) -> bool:
        return self._is_client

    def __eq__(self, other) -> bool:
        return self.get_id() == other.get_id()

    def __str__(self) -> str:
        return "Controller(" + str(self.get_id()) + ", " + self.get_address() + ")"

    def to_proto(self) -> controller:
        return controller(
            name = self.get_name(),
            address = self.get_address(),
            credentials = self.get_credentials().to_proto(),
            is_client = self.is_client()
        )

    @classmethod
    def from_proto(Class, proto):
        name = proto.name
        address = proto.address
        credentials = Credentials.from_proto(proto.credentials)
        is_client = proto.is_client
        return Class(name, address, credentials, is_client = is_client)

class LocalController(StubController):
    def __init__(self,
            name: str,
            address: str,
            credentials: Credentials,
            mac: str,
            concentrator: bool,
            ip: Address,
            is_client: bool = False
        ):
        super().__init__(name, address, credentials, is_client=is_client)
        self._mac = mac
        self._concentrator = concentrator
        self._ip = ip

    def get_mac(self) -> str:
        return self._mac

    def is_concentrator(self) -> bool:
        return self._concentrator

    def get_ip(self) -> Address:
        return self._ip

    def to_proto(self) -> local_controller:
        return local_controller(
            controller = super().to_proto(),
            mac = self.get_mac(),
            concentrator = self.is_concentrator(),
            ip = self.get_ip().packed,
            is_client = self.is_client()
        )

    @classmethod
    def from_proto(Class, proto: local_controller):
        name = proto.controller.name
        address = proto.controller.address
        credentials = Credentials.from_proto(proto.controller.credentials)
        is_client = proto.controller.is_client
        mac = proto.mac
        concentrator = proto.concentrator
        ip = ip_address(proto.ip)

        return Class(name, address, credentials, mac, concentrator, ip, is_client=is_client)
