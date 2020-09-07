
from pydantic import BaseModel, Field, constr

Name = {
    "default": None,
    "title": "Database name",
    "desription": "Lowercase alphanumeric characters only with hyphens/underscores, maximum 32 digits",
    "regex": r"^[a-zA-Z0-9]+[a-zA-Z0-9_\-]*[a-zA-Z0-9]+$",
    "min_length": 1,
    "max_length": 32
}

class Database(BaseModel):
    name: str = Field(**Name)    

class PasswordReset(BaseModel):
    password: str