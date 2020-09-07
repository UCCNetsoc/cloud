
import time
from typing import Union, List, Optional
from pydantic import BaseModel, constr, EmailStr, Field

from .account import Username
from .jwt import Payload, Serialized

from . import group
from typing import List

Password = {
    "default": None,
    "title": "Password",
    "description": "8 to 128 characters long",
    "min_length": 8,
    "max_length": 128
}

class Reset(Payload):
    """
    Represents info about a password reset
    This is normally emailed (serialized as a jwt) to a user to verify their email, they pass it back to us
    We verify, check the username and let them reset their password
    """
    sub: constr(regex=r'^admin password reset') = "admin password reset"
    username: str = Field(**Username)

class New(BaseModel):
    """
    Information about the new password they want to have

    reset contains the serialized JWT of Reset
    password contains the new password they want
    """
    reset: Serialized 
    password: str = Field(**Password)