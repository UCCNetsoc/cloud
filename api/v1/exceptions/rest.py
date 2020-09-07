
from .exception import APIException

from v1 import models

class RESTException(APIException):
    def __init__(self):
        super().__init__()

class Error(RESTException):
    status_code: int
    error_model: models.rest.Error

    def __init__(self, status_code: int, detail: models.rest.Detail):
        super().__init__()
        self.error_model = models.rest.Error(detail=detail)
        self.status_code = status_code

    def __str__(self):
        return f"{self.status_code}: {self.error_model.detail.msg}: {self.error_model.detail.loc or []}"