from typing import Optional, Union, List
from pathlib import Path
from enum import Enum
from pydantic import BaseModel, constr, EmailStr, Field
from typing import Set


import ipaddress
import socket
import yaml
import time

from .account import Username

Name = {
    "default": None,
    "alias": "name",
    "title": "Website name",
    "description": "Only lowercase alphabetical characters with hyphens allowed",
    "regex": r"^[a-zA-Z_-]+$",
}

Host = {
    "default": None,
    "alias": "host",
    "title": "Website host",
    "description": "Any valid domain",
    "regex": r"^((?!-))(xn--)?[a-z0-9][a-z0-9-_]{0,61}[a-z0-9]{0,1}\.(xn--)?([a-z0-9\-]{1,61}|[a-z0-9-]{1,30}\.[a-z]{2,})$"
}

class Software(str, Enum):
    NotInstalled = "not-installed"
    Wordpress = "wordpress"
    PHPInfo = "php-info"
    Unknown = "unknown"
    Custom = "custom-user-data"

class SoftwareArgs(BaseModel):
    pass

class WordpressSoftwareArgs(SoftwareArgs):
    pass
    # db_name: str
    # db_username: str
    # db_password: str
    # db_host: str

class Runtime(str, Enum):
    PHP = "php"

class Config(BaseModel):
    hosts: Set[constr(regex=Host["regex"])] = set()
    runtime: str = Runtime.PHP

class Website(BaseModel):
    """
        Represents a website    
    """
    name: str = Field(**Name)
    root: Path
    username: str = Field(**Username)
    config: Config
    valid: bool
    remarks: List[str]
    software: Software
    uid: int = 65534

        