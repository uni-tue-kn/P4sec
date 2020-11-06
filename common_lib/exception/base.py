
class Base(Exception):
    def __init__(self, message=""):
        super(Base, self).__init__(message)
        self.message = message

    def __str__(self):
        return self.message
