# common
from common_lib.credentials import Credentials
from common_lib.controller import Settings

# protobuf / grpc
from controller_pb2_grpc import RegistrationStub # type: ignore
from controller_pb2 import controller, registration # type: ignore

# other
from grpc import Channel # type: ignore
from uuid import UUID
from typing import Optional, Set, Callable

class Registration:

    def __init__(self, channel: Channel, name: str, address: str, credentials: Credentials):
        self._stub = RegistrationStub(channel)
        self._name = name
        self._address = address
        self._credentials = credentials
        self._registration = None # type: Optional[ registration ]
        self._registration_handlers = set() # type: Set[ Callable[ [ UUID ], None ] ]

    def on_register(self, handler: Callable[ [ UUID ], None ]) -> None:
        self._registration_handlers.add(handler)

    def register(self) -> None:
        request = controller(
            name = self._name,
            address = self._address,
            credentials = self._credentials.to_proto(),
        )

        self.set_registration(self._stub.register(request))

    def unregister(self) -> None:
        self._stub.unregister(self.get_registration())

    def set_registration(self, registration: registration) -> None:
        assert self._registration is None, "Already registered"
        self._registration = registration
        for handler in self._registration_handlers:
            handler(self.get_id())

    def get_registration(self) -> registration:
        assert self._registration is not None, "Not registered."
        return self._registration

    def get_id(self) -> UUID:
        return UUID(self.get_registration().id)
