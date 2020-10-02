
from typing import Optional, Union, List
from pydantic import BaseModel, constr, EmailStr, Field, constr

class Captcha(BaseModel):
    """
        Represents a request body that requires a captcha token
    """
    captcha: str = ""
