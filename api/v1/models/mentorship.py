
from pydantic import BaseModel
from typing import Optional

class Mentorship(BaseModel):
    title: str
    description: str
    teacher: str

class Enrollment(BaseModel):
    """Represents a request to be mentored"""
    reason: str