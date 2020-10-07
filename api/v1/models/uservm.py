
import datetime
import ipaddress


from typing import Optional, Union, List
from pydantic import BaseModel, constr, EmailStr, Field, constr
from enum import Enum

from .account import Username

fqdn = "uservm.netsoc.co"

class PortMapping(BaseModel):
    target: int
    published: int

Hostname = {
    "default": None,
    "title": "VM Hostname",
    "description": "",
    "regex": r"^[a-z0-9-.]+$",
    "max_length": 24
}

FQDN = {
    "default": None,
    "title": "VM FQDN",
    "description": "",
    "regex": r"^[a-z0-9-.]+." + fqdn + r"$",
    "max_length": 150 
}


class Specs(BaseModel):
    # number of vcores
    cores: int

    # number of gb of disk
    disk_space: int

    # number of mb of ram
    memory: int

class Image(BaseModel):
    class DiskFormat(str, Enum):
        QCOW2: str = "qcow2"

    
    title: str
    description: str
    logo_url: str
    disk_url: str
    disk_sha256sums_url: str
    disk_format: str = DiskFormat.QCOW2
    specs: Specs


ImageID = {
    "default": None,
    "title": "VM Hostname",
    "description": "",
    "regex": r"^[a-z0-9-.]+$",
    "min_length": 1,
    "max_length": 32
}

class Provision(BaseModel):
    class Stage(str, Enum):
        # VM request status
        AwaitingApproval = "awaiting-approval"
        Approved = "approved"
        DownloadImage = "installation-downloading-image"
        PushImage = "installation-push-image"
        SetSpecs = "installation-set-specs"
        FlashImage = "installation-flash-image"
        CloudInitSetup = "installation-setup-cloud-init"
        Installed = "installed"
        Failed = "installation-failed"

    stage: Stage = Stage.AwaitingApproval
    remarks: List[str] = []
    image: Image

class Inactivity(BaseModel):
    # The date they last set the VM as active
    last_marked_active: datetime.date

    # The last time we emailed them about the VM being inactive
    last_emailed_about_inactivity: datetime.date = None

    # The last time we emailed them about impending deletion
    last_emailed_about_impending_deletion: datetime.date = None

    # Number of inactive emails we've sent
    inactivity_email_count: int = 0

    # Number of deletion warning emails we've sent
    impending_deletion_email_count: int = 0

class NICAllocation(BaseModel):
    addresses: List[ipaddress.IPv4Interface] = []
    gateway4: ipaddress.IPv4Address
    macaddress: str

class Network(BaseModel):
    ports: List[PortMapping] = []
    domains: List[str] = []
    nic_allocation: NICAllocation 

class Metadata(BaseModel):
    groups: List[str] = ["vm", "uservm"]
    host_vars: dict = {}

    # VM owner
    owner: str = Field(**Username)

    # Why the VM exists
    reason: str 

    # Info about the VM provisioning
    provision: Provision

    # Inactivity data
    inactivity: Inactivity

    # Network
    network: Network

class Status(str, Enum):
    NotApplicable = 'N/A'
    Stopped = 'Stopped'
    Starting = 'Starting'
    Running = 'Running'
    Failed = 'Failed - Restart / Contact SysAdmins'

class UserVM(BaseModel):
    # Proxmox node
    node: str 

    # VM id
    id: int

    # VM hostname
    hostname: str = Field(**Hostname)

    # VM fqdn
    fdqn: str = Field(**FQDN)

    # Specs
    specs: Specs

    # Metadata
    metadata: Metadata

    # Remarks about the VM and it's configuration we return to the user
    remarks: List[str] = []

    status: Status

