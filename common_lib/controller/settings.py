# common
from common_lib.credentials import Credentials

# other
from json import load
from typing import Dict

class SubSettings:

    def __init__(self, data: Dict) -> None:
        self._data = data

    def get_data(self, path: str):
        return self._data[path]

    def has(self, path: str) -> bool:
        return path in self._data

class Settings(SubSettings):

    def __init__(self, args) -> None:
        super().__init__(load(open(args.config)))
        self._args = args

    def get_args(self):
        return self._args

    def is_verbose(self) -> bool:
        return self.get_args().verbose

    def is_interactive(self) -> bool:
        return self.get_args().interactive

class ControllerSettings(Settings):

    def __init__(self, args) -> None:
        super().__init__(args)

    def get_name(self) -> str:
        return str(self.get_data("name"))

    def get_address(self) -> str:
        return str(self.get_data("address"))

    def get_credentials(self) -> Credentials:
        return Credentials.read_from(self.get_data("credentials"))

class TargetSettings(SubSettings):

    def __init__(self, data: Dict) -> None:
        super().__init__(data)

    def get_name(self) -> str:
        return self.get_data("name")

    def get_address(self) -> str:
        return self.get_data("address")

    def get_credentials(self) -> Credentials:
        return Credentials.read_from(self.get_data("credentials"))
