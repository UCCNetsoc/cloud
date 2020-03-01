
from pydantic import BaseModel, constr, EmailStr

from . import group
from typing import List

class DisplayName(constr(regex=r"^[A-Za-zÀ-ÿ \(\)\&\-\.]+")):
    pass

class UserName(constr(regex=r"^[a-z0-9]([a-z0-9\-\_]{1,15}[a-z0-9])$", min_length=1, max_length=16)):
    pass

class Password(constr(min_length=8, max_length=32)):
    pass

class Account(BaseModel):
    """
        Represents info about an nsa3 account
    """
    displayname:    DisplayName
    username:       UserName
    email:          EmailStr
    groups:         List[group.Group]