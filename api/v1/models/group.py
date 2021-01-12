
from pydantic import BaseModel, Field
from typing import Optional

GroupName = Field(None, title="Group Name", description="Lowercase alphanumeric characters only, maximum 16 digits", regex=r"^[a-z0-9]([a-z0-9\-\_]{1,15}[a-z0-9])$", min_length=1, max_length=16)

class Group(BaseModel):
    group_name: str = GroupName
    description: Optional[str]
    gid: Optional[int]

NetsocAccount = Group(group_name="netsoc_account", description="Netsoc Account", gid=422)
NetsocCommittee = Group(group_name="netsoc_committee", description="Netsoc Committee", gid=421)
NetsocSysAdmin = Group(group_name="netsoc_sysadmin", description="Netsoc SysAdmin", gid=420)
    
groups = [NetsocAccount, NetsocCommittee, NetsocSysAdmin]
