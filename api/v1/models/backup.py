from typing import Optional, Union, List
from pathlib import Path
from pydantic import BaseModel, constr

from .account import Account
from .jwt import Payload

import time

class Backup(BaseModel):
    """
    Represents a possible backup belonging to a user, Path can be a file or folder
    """

    name: str
    path: Path
    uid: int

class Request(Payload):
    """
    Represents info about a request to download a users backup. This is normally signed and serialized as a JWT
    """
    sub: constr(regex=r'^admin backup request$') = "admin backup request"
    backup: Backup
