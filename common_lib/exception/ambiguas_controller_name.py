from common_lib.exception.base import Base

from typing import List

class AmbiguasControllerName(Base):

    def __init__(self, name: str, controllers: List):
        super().__init__()
        self._name = name
        self._controllers = controllers

    def get_name(self) -> str:
        return self._name

    def get_controllers(self) -> List:
        return self._controllers

    def __str__(self):
        return "Ambiguas controller name \"" + self.get_name() + "\": " + \
                ", ".join(str(x) for x in self.get_controllers())
