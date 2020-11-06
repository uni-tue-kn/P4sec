# common
from common_lib.credentials import Credentials
from common_lib.stub import Registration as Base

# local
from local_lib.settings import Settings

# other
from controller_pb2 import local_controller, controller # type: ignore
from uuid import UUID
from grpc import Channel # type: ignore

class Registration(Base):

    def __init__(self, channel: Channel, settings: Settings) -> None:
        super().__init__(channel, settings.get_name(), settings.get_address(),
                settings.get_credentials())
        self._lc_settings = settings

    def register(self) -> None:
        request = local_controller(
            controller = controller(
                name = self._lc_settings.get_name(),
                address = self._lc_settings.get_address(),
                credentials = self._lc_settings.get_credentials().to_proto()
            ),
            mac = self._lc_settings.get_mac(),
            concentrator = self._lc_settings.is_concentrator(),
            ip = self._lc_settings.get_ip().packed
        )
        self.set_registration(self._stub.register_local_controller(request))

    def get_key(self) -> bytes:
        # TODO make key manager
        return self.get_registration().key
