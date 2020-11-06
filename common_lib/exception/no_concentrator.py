from common_lib.exception import Base

class NoConcentrator(Base):
    def __init__(self):
        Base.__init__(self, "Network has no concentrator.")
