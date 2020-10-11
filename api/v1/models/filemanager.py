from typing import Optional, Union, List
from pathlib import Path
from pydantic import BaseModel, constr

from .account import Account
from .jwt import Payload

import time
import os

class Stat(BaseModel):
    isdir: bool
    size: int
    uid: int
    gid: int
    last_edited: int
    perms: str
