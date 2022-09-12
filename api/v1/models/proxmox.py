
import datetime
import ipaddress

from typing import Optional, Union, List, Dict, Tuple, Set
from pydantic import BaseModel, constr, EmailStr, Field, conint
from enum import Enum

from .account import Username

Hostname = {
    "default": None,
    "title": "VM Hostname",
    "description": "Alphanumeric with hyphens allowed, no spaces",
    "regex": r"^[a-z0-9-]+$",
    "max_length": 24
}

Reason = {
    "default": None,
    "title": "Reason",
    "description": "A concise reason as to what you will use the VM/Container for",
    "max_length": 280
}

FQDN = {
    "default": None,
    "title": "FQDN",
    "description": "",
    "regex": r"^[a-z0-9-.]+.$",
    "max_length": 150 
}

VHost = {  
    "default": None,
    "title": "Website domain/hostname",
    "description": "Any valid domain name",
    "regex": r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$"
}

TemplateID = {
    "default": None,
    "title": "Template ID",
    "description": "Template ID",
    "regex": r"^[a-z0-9-.]+$",
    "min_length": 1,
    "max_length": 32
}

class Type(str, Enum):
    LXC: str = "lxc"
    VPS: str = "vps"

def generate_ranged_port_field_args(gte, lte):
    return {
        "default": None,
        "title": "Port number",
        "description": "Port number in range [{gte},{lte}]",
        "ge": gte,
        "le": lte
    }

Port = {
    "default": None,
    "title": "Port number",
    "description": "Any port number",
    "gt": 0,
    "le": 65535
}

class Specs(BaseModel):
    # number of vcores
    cores: int

    # number of gb of disk
    disk_space: int


    # number of mb of ram
    memory: int

    # swap
    swap: int = 0

class TemplateMetadata(BaseModel):
    title: str
    subtitle: str
    description: str
    logo_url: str
    wake_on_request: bool

class Template(BaseModel):
    type: Type
    id: int
    fqdn: str
    node: str
    hostname: str
    metadata: TemplateMetadata
    specs: Specs

from .account import Username
from .jwt import Payload, Serialized
    
class ToS(BaseModel):
    suspended: bool = False
    reason: Optional[str] = None

class Inactivity(BaseModel):
    marked_active_at: datetime.date

    # The last time we emailed them about the VM impending inactivity shutdown
    emailed_shutdown_warning_at: datetime.date = None

    # The last time we emailed them that the VM is now inactive and shutdown
    emailed_shutdown_at: datetime.date = None

    # The last time we emailed them about impending deletion
    emailed_deletion_warning_at: datetime.date = None

    # Number of inactive shutdown emails we've sent
    shutdown_warning_email_count: int = 0

    # Number of 'VM now inactive and shutdown' emails we've sent
    shutdown_email_count: int = 0

    # Number of deletion warning emails we've sent
    deletion_warning_email_count: int = 0

class RootUser(BaseModel):
    password_hash: str
    ssh_public_key: str
    
class NICAllocation(BaseModel):
    addresses: List[ipaddress.IPv4Interface] = []
    gateway4: ipaddress.IPv4Address
    macaddress: str
    vlan: Optional[int]

class VHostOptions(BaseModel):
    port: int = Field(**Port)
    https: bool = False

class Network(BaseModel):
    vhosts: Dict[str,VHostOptions] = {}
    ports: Dict[int, int] = {}
    nic_allocation: NICAllocation 

class InstanceRequestDetail(BaseModel):
    template_id: str = Field(**TemplateID)
    reason: str = Field(**Reason)

class InstanceRequest(Payload):
    sub: constr(regex=r'^admin instance request$') = "admin instance request"
    username: str = Field(**Username)
    hostname: str = Field(**Hostname)
    type: Type
    detail: InstanceRequestDetail

class InstanceRequestDenial(BaseModel):
    reason: Optional[str] = "-"

class RespecRequest(BaseModel):
    details: str

class Metadata(BaseModel):
    groups: List[str] = []
    host_vars: dict = {}

    owner: str = Field(**Username)

    # Tracks ToS suspension status
    tos: ToS = ToS()

    # Is this a permanent instance? i.e dedicated towards sysadmins and the like
    permanent: bool = False 

    # Inactivity data
    inactivity: Inactivity

    # Wake-On-Request
    wake_on_request: bool

    # Network
    network: Network

    # Root user info
    root_user: RootUser

    template_metadata: Optional[TemplateMetadata]
    reason: Optional[str]

class Status(str, Enum):
    NotApplicable = 'N/A'
    Stopped = 'Stopped'
    Running = 'Running'

class Instance(BaseModel):
    type: Type

    # Proxmox node
    node: str 

    # VM id
    id: int

    # VM hostname
    hostname: str = Field(**Hostname)

    # VM fqdn
    fqdn: str = Field(**FQDN)

    # Specs
    specs: Specs

    # If the VM is currently marked as active
    active: bool
    
    # Future dates for shutdown and deletion
    inactivity_shutdown_date: datetime.date
    inactivity_deletion_date: datetime.date

    # Metadata
    metadata: Metadata

    # Remarks about the VM and it's configuration we return to the user
    remarks: List[str] = []

    status: Status

    disk: int
    mem: int
    uptime: int