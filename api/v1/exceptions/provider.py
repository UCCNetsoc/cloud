from .exception import APIException

class ProviderException(APIException):
    def __init__(self, reason):
        super().__init__(reason)


class Unavailable(ProviderException):
    def __init__(self, reason):
        super().__init__(f"Provider unavailable: {reason}")

class Failed(ProviderException):
    def __init__(self, reason):
        super().__init__(f"Provider failed: {reason}")