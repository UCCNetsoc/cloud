from typing import Optional, Union, List
from pathlib import Path
from pydantic import BaseModel

from .account import Account
from .jwt import Payload

import time
import os
import paramiko

class Stat(BaseModel):
    paramiko.SFTPAttributes

class DirStat(BaseModel):
    filename: os.stat_result

class Dest(BaseModel):
    path: str=Path(default="/")