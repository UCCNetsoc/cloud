
from pydantic import BaseModel
from pathlib import Path
from typing import Set, List, Dict, Optional
from v1 import models

class Auth(BaseModel):
    direct_grant_url: str = "http://keycloak.netsoc.dev/auth/realms/freeipa/protocol/openid-connect/auth"

    class JWT(BaseModel):
        public_key: str

    jwt: JWT

class Accounts(BaseModel):
    home_dirs: Path
    username_blacklist: List[str]

    class FreeIPA(BaseModel):
        server: str
        username: str
        password: str

    freeipa: FreeIPA


class Email(BaseModel):
    from_name: str = "UCC Netsoc Admin"
    from_address: str = "netsocadmin@netsoc.co"
    reply_to_address: str = "netsoc@uccsocieties.ie"

    class SendGrid(BaseModel):
        key: str

    sendgrid: SendGrid

class Links(BaseModel):
    base_url: str = "https://admin.netsoc.co"
    
    class JWT(BaseModel):
        public_key: str
        private_key: str

    jwt: JWT

class MySQL(BaseModel):
    server: str
    username: str
    password: str

class Websites(BaseModel):
    folder: str = "www"
    config_filename: str = "netsoc.json"
    
    class DNS(BaseModel):
        base_domain: str = "netsoc.co"
        txt_name: str = "_netsoc"
        allowed_a_aaaa: Set[str] = set(["84.39.234.50", "84.39.234.51"])
    
    dns: DNS 

from . import mentorship

class Mentorships(BaseModel):
    available: Dict[str, mentorship.Mentorship]

class WebserverConfigurator(BaseModel):
    push_interval: int = 25

    class Unit(BaseModel):
        class BasicAuth(BaseModel):
            username: str
            password: str

        basic_auth: BasicAuth
        targets: List[str]

    unit: Unit


class Metrics(BaseModel):
    port: int = 8000

class Webhooks(BaseModel):
    form_filled: str
    info: str

class MkHomeDir(BaseModel):
    pass

class Backups(BaseModel):
    folder: str = ".snaps"

class HomeDirConsistency(BaseModel):
    scan_interval: int

class Hcaptcha(BaseModel):
    secret: Optional[str]
    url = "https://hcaptcha.com/siteverify"

class Config(BaseModel):
    production: bool = False
    home_dirs: Path = Path("/home/users")
    accounts: Accounts
    auth: Auth
    email: Email
    links: Links
    mysql: MySQL
    backups: Backups
    websites: Websites
    webhooks: Webhooks
    mentorships: Mentorships
    webserver_configurator: WebserverConfigurator
    homedir_consistency: HomeDirConsistency
    metrics: Metrics
    hcaptcha: Optional[Hcaptcha]