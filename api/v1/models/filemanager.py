from typing import Optional, Union, List
from pathlib import Path
from pydantic import BaseModel, constr

from .account import Account
from .jwt import Payload

import time

class Download(BaseModel):
    path: str
    uid: int

class Request(Payload):
    """
    Represents info about a request to download a users file/directory. This is normally signed and serialized as a JWT
    """
    sub: constr(regex=r'^admin download request$') = "admin download request"
    download: Download


class FileList(BaseModel):
    path: str
    filenames: [str]
