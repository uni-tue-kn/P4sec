from common_lib.exception import Base

class FileNotFound(Base):
    def __init__(self, path):
        super(FileNotFound, self).__init__()
        self.path = path

    def __str__(self):
        return "Could not find file: " + self.path
