from pydantic import BaseModel
from typing import Optional, List

class Detail(BaseModel):
    msg: str
    loc: Optional[List[str]]

class Error(BaseModel):
    detail: Detail

class Info(BaseModel):
    detail: Detail