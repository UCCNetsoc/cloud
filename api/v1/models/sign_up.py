from typing import Optional, Union, List
from pydantic import BaseModel, constr, EmailStr, Field, constr

from .account import Username
from .password import Password
from .jwt import Payload

import time

class SignUp(BaseModel):
    """
    Represents a request to create an account
    """
    email: EmailStr
    username: str = Field(**Username)
    password: str = Field(**Password)

UCCStudentEmail = Field(None, alias="email", title="UCC Student Email", description="<student id>@umail.ucc.ie", regex=r"^[0-9]{8,11}@umail\.ucc\.ie$")
UCCStaffEmail   = Field(None, alias="email", title="UCC Staff Email",   description="<email>@ucc.ie", regex=r"^[a-zA-Z\.]+@ucc.ie$")
UCCSocietyEmail = Field(None, alias="email", title="UCC Society Email", description="<email>@uccsocieties.ie", regex=r"^[a-zA-Z\.]+@uccsocieties.ie$")

class UCCStudent(SignUp):
    aemail: str = UCCStudentEmail

class UCCStaff(SignUp):
    aemail: str = UCCStaffEmail

class UCCSociety(SignUp):
    aemail: str = UCCSocietyEmail 

class Verification(Payload):
    """
    Represents info about a sign-up needing verification (as a JWT).
    This is normally emailed (signed as a jwt) to a user to verify their email, they pass it back to us
    We verify, check the username and mark their account as verified
    """
    sub: constr(regex=r'^admin account verification') = "admin account verification"
    username: str = Username