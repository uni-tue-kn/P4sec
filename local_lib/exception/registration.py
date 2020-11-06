class RegistrationException(Exception):

    def __init__(self, reason):
        super().__init__()
        self.reason = reason

    def __str__(self):
        return "Could not register at global controller: " + str(self.reason)
