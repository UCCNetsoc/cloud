
class APIException(Exception):
    reason: str

    def __init__(self, reason):
        super().__init__()
        self.reason = reason

    def __str__(self):
        return self.reason

    def __repr__(self):
        return self.reason