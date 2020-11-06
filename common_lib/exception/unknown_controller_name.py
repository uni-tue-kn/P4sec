from common_lib.exception.base import Base

class UnknownControllerName(Base):

    def __init__(self, name: str):
        super().__init__("Unknown controller name \"" + name + "\"")
