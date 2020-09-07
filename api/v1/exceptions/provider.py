from .exception import APIException

class ProviderException(APIException):
    def __init__(self):
        super().__init__()


class Unavailable(ProviderException):
    reason: str

    def __init__(self, reason):
        super().__init__()
        self.reason = reason

    def __str__(self):
        return f"Provider unavailable: {self.reason}"

class Failed(ProviderException):
    reason: str

    def __init__(self, reason):
        super().__init__()
        self.reason = reason

    def __str__(self):
        return f"Provider failed: {self.reason}"