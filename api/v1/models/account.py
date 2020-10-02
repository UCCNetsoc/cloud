
from pydantic import BaseModel, constr, EmailStr, Field
from pathlib import Path
from typing import Union, Optional, Dict

from . import group

from typing import List


Username = {
    "default": None,
    "title": "Username",
    "description": "Lowercase alphanumeric characters only, maximum 16 digits",
    "regex": r"^[a-z0-9]([a-z0-9\-\_]{1,15}[a-z0-9])$",
    "min_length": 1,
    "max_length": 16
}

class Account(BaseModel):
    """
        Represents info about an admin account
    """
    username: str = Field(**Username)
    email: Optional[EmailStr]

    verified: bool = False

    # only on verified accounts
    
    uid: Optional[int] = 65534
    groups: Dict[str, group.Group] = {}
    home_dir: Union[Path, None] = None