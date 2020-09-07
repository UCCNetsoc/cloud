

from .exception import APIException

class ResourceException(APIException):
    def __init__(self):
        super().__init__()

class AlreadyExists(ResourceException):
    reason: str
    
    def __init__(self, reason: str = "The specified resource already exists"):
        super().__init__()
        self.reason = reason

    def __str__(self):
        return self.reason

class NotFound(ResourceException):
    reason: str
    
    def __init__(self, reason: str = "The specified resource was not found"):
        super().__init__()
        self.reason = reason

    def __str__(self):
        return self.reason


class Unavailable(ResourceException):
    reason: str
    
    def __init__(self, reason: str = "The specified resource was unavailable"):
        super().__init__()
        self.reason = reason

    def __str__(self):
        return self.reason