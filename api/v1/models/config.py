
import ipaddress

from pydantic import BaseModel
from pathlib import Path
from typing import Set, List, Dict, Optional, Tuple
from v1 import models

class Auth(BaseModel):
    direct_grant_url: str = "http://keycloak.netsoc.dev/auth/realms/freeipa/protocol/openid-connect/auth"

    class JWT(BaseModel):
        public_key: str

    jwt: JWT

class Accounts(BaseModel):
    home_dirs: Path = Path("/home/users")
    username_blacklist: List[str] = [
        # vps and container _must_ be blacklisted
        "vps",
        "ssh",
        "sftp",
        "container",
        "api",
        "proxy"
        "_apt",
        "admin",
        "apache2",
        "api",
        "backup",
        "bareos",
        "bigbertha",
        "bin",
        "bind",
        "blog",
        "boole",
        "ci",
        "cloud",
        "colord",
        "control",
        "cron",
        "daemon",
        "dnsmasq",
        "docker",
        "fail2ban",
        "feynman",
        "games",
        "gnats",
        "httpd",
        "infra",
        "irc",
        "ircd",
        "ldap",
        "leela",
        "libvirt-dnsmasq",
        "libvirt-qemu",
        "list",
        "lovelace",
        "lp",
        "lxd",
        "mail",
        "man",
        "messagebus",
        "mysql",
        "netsoc",
        "news",
        "nobody",
        "ntp",
        "portainer",
        "postfix",
        "postgres",
        "proxy",
        "redis",
        "root",
        "sshd",
        "sync",
        "sys",
        "syslog",
        "systemd-bus-prox",
        "systemd-bus-proxy",
        "systemd-network",
        "systemd-resolve",
        "systemd-timesync",
        "thief",
        "unf2b",
        "uucp",
        "uuidd",
        "wiki",
        "www-data"
    ]

    class FreeIPA(BaseModel):
        server: str
        username: str
        password: str

    freeipa: FreeIPA

class Email(BaseModel):
    from_name: str = "Netsoc Cloud"
    from_address: str = "cloud@netsoc.co"
    reply_to_address: str = "netsoc@uccsocieties.ie"

    class SendGrid(BaseModel):
        key: str

    sendgrid: SendGrid

class Links(BaseModel):
    base_url: str = "https://netsoc.cloud"
    
    class JWT(BaseModel):
        public_key: str
        private_key: str

    jwt: JWT

class Metrics(BaseModel):
    port: int = 8000

class Webhooks(BaseModel):
    form_filled: str
    info: str

class MkHomeDir(BaseModel):
    pass

class Captcha(BaseModel):
    class Hcaptcha(BaseModel):
        secret: Optional[str]
        url: str = "https://hcaptcha.com/siteverify"
    
    hcaptcha: Optional[Hcaptcha]
    enabled: bool = False

from .proxmox import Template
class Proxmox(BaseModel):
    class Cluster(BaseModel):
        class SSH(BaseModel):
            server: str
            port: str = 22
            username: str = "root"
            password: str

        class API(BaseModel):
            server: str
            port: str
            username: str = "root@pam"
            token_name: str
            token_value: str

        api: API
        ssh: SSH

    class VPS(BaseModel):
        base_fqdn: str = "vps.netsoc.cloud"
        templates: Dict[str, Template] = {}
        dir_pool: str = "local"

        inactivity_shutdown_warning_num_days: int = 30
        inactivity_shutdown_num_days: int = 60
        inactivity_deletion_warning_num_days: int = 90
        inactivity_deletion_num_days: int = 120

    class LXC(BaseModel):
        base_fqdn: str = "container.netsoc.cloud"
        templates: Dict[str, Template] = {}

        inactivity_shutdown_warning_num_days: int = 60
        inactivity_shutdown_num_days: int = 90
        inactivity_deletion_warning_num_days: int = 120
        inactivity_deletion_num_days: int = 150

    class Network(BaseModel):
        class PortForward(BaseModel):
            range: Tuple[int,int] = (16384,32767)

        class VHostRequirements(BaseModel):
            class UserSupplied(BaseModel):
                verification_txt_name: str
                allowed_a_aaaa: Set[str]

            base_domain: str
            user_supplied: UserSupplied

        # class VLANJumpHost(BaseModel):
        #     server: str
        #     port: str = 22
        #     username: str = "jumphost"
        #     public_key: Optional[str] = None
        #     private_key: Optional[str] = None
        #     password: str = None

        traefik_config_key: str
        bridge: str = "vmbr0"
        vlan: int = 40
        gateway: ipaddress.IPv4Address = ipaddress.IPv4Address("10.40.0.1")
        network: ipaddress.IPv4Interface = ipaddress.IPv4Interface("10.40.0.0/16")
        range: Tuple[ipaddress.IPv4Address, ipaddress.IPv4Address] = (
            ipaddress.IPv4Address("10.40.0.3"),
            ipaddress.IPv4Address("10.40.0.254")
        )

        #vlan_jumphost: VLANJumpHost

        port_forward: PortForward
        vhosts: VHostRequirements


    blacklisted_nodes: List[str]
    cluster: Cluster
    lxc: LXC
    vps: VPS
    network: Network

    dir_pool: str = "local"

class Config(BaseModel):
    production: bool = False
    accounts: Accounts
    auth: Auth
    email: Email
    links: Links
    webhooks: Webhooks
    metrics: Metrics = Metrics()
    captcha: Optional[Captcha]
    proxmox: Proxmox
