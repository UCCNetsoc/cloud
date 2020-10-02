

from .exception import APIException

class ResourceException(APIException):
    def __init__(self, reason):
        super().__init__(reason)


class AlreadyExists(ResourceException):
    def __init__(self, reason: str = "The specified resource already exists"):
        super().__init__(reason)
        self.reason = reason

class NotFound(ResourceException):
    def __init__(self, reason: str = "The specified resource was not found"):
        super().__init__(reason)


class Unavailable(ResourceException):
    def __init__(self, reason: str = "The specified resource was unavailable"):
        super().__init__(reason)

