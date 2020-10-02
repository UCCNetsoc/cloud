
from .exception import APIException

from v1 import models

class Error(APIException):
    status_code: int
    detail: models.rest.Detail

    def __init__(self, status_code: int, detail: models.rest.Detail):
        self.status_code = status_code
        self.error_model = models.rest.Error(
            detail=detail
        )
        super().__init__(f"{self.status_code}: {self.error_model.detail.msg}: {self.error_model.detail.loc or []}")
