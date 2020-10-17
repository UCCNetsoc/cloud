
import random
import yaml
import datetime
import requests
import hashlib
import os
import socket
import shutil
import paramiko
import dns
import dns.resolver
import dns.exception
import ipaddress
import io
import crypt
import string
import time
import structlog as logging

from urllib.parse import urlparse, unquote

from typing import Optional, Tuple, List, Dict, Union
from proxmoxer import ProxmoxAPI

from v1 import models, exceptions, utilities
from v1.config import config

logger = logging.getLogger(__name__)

class ProxmoxNodeSSH:
    """Paramiko SSH client that will first SSH into an exposed Proxmox node, then jump into any of the nodes in the Cluster"""

    jump: paramiko.SSHClient
    ssh: paramiko.SSHClient
    node_name: str

    ssh: paramiko.SSHClient
    sftp: paramiko.SFTPClient

    def __init__(self, node_name: str):
        self.jump = paramiko.SSHClient()
        self.ssh = paramiko.SSHClient()
        self.node_name = node_name

    def __enter__(self):
        self.jump.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.jump.connect(
            hostname=config.proxmox.ssh.server,
            username=config.proxmox.ssh.username,
            password=config.proxmox.ssh.password,
            port=config.proxmox.ssh.port
        )

        self.jump_transport = self.jump.get_transport()
        self.jump_channel = self.jump_transport.open_channel("direct-tcpip", (self.node_name, 22), ("127.0.0.1", 22))

        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(
            self.node_name, # nodes should be setup in /etc/hosts correctly
            username=config.proxmox.ssh.username,
            password=config.proxmox.ssh.password,
            port=22,
            sock=self.jump_channel
        )

        self.sftp = self.ssh.open_sftp()

        return self

    def __exit__(self, type, value, traceback):
        self.sftp.close()
        self.ssh.close()
        self.jump.close()

class Proxmox():
    def __init__(self):
        self.prox = ProxmoxAPI(
            host=config.proxmox.api.server,
            user=config.proxmox.api.username,
            password=config.proxmox.api.password,
            port=config.proxmox.api.port,
            verify_ssl=False
        )

    def _select_best_node(
        self,
        specs: models.proxmox.Specs
    ) -> Optional[str]:
        """Finds a good node based off specs given"""
        nodes = self.prox.nodes.get()

        if len(nodes) == 0:
            return None
        
        choice = nodes[0]["node"]

        scoreboard = {}
        for node in nodes:
            node_name = node['node']
            
            if node_name not in scoreboard:
                scoreboard[node_name] = 0

            if (node['maxmem'] - node['mem']) > (specs.memory*1000000):
                scoreboard[node_name] += 1

            if (node['mem']/node['maxmem']) < 0.6:
                scoreboard[node_name] += 1
            
            if (node['maxcpu'] >= specs.cores):
                scoreboard[node_name] += 1

        # return the node with the highest score
        return sorted(scoreboard, key=scoreboard.get, reverse=True)[0]

    def _get_lxc_fqdn_for_username(
        self,
        username: str,
        hostname: str
    ) -> str:
        return f"{hostname}.{username}.{config.proxmox.lxc.base_fqdn}"

    def _get_lxc_fqdn_for_account(
        self,
        account: models.account.Account,
        hostname: str
    ) -> str:
        return self._get_lxc_fqdn_for_username(account.username, hostname)

    def _allocate_ip_lxc(
        self
    ) -> ipaddress.IPv4Interface:
        offset_ip = (config.proxmox.lxc.network.ip + 1) + random.randint(1,config.proxmox.lxc.network.network.num_addresses-3)
        assigned_ip_and_netmask = f"{offset_ip}/{config.proxmox.lxc.network.network.prefixlen}"

        return ipaddress.IPv4Interface(assigned_ip_and_netmask)

    def _random_password(
        self,
        length=24
    ) -> str:
        return ''.join(random.choice(string.ascii_letters) for i in range(length))

    def _hash_password(
        self,
        password: str
    ) -> str:
        return crypt.crypt(password, crypt.METHOD_SHA512)

    def _serialize_metadata(
        self,
        metadata: Union[models.proxmox.LXCMetadata, models.proxmox.VPSMetadata]
    ):
        # https://github.com/samuelcolvin/pydantic/issues/1043
        return yaml.safe_dump(
            yaml.safe_load(metadata.json()),
            default_flow_style=False,
            explicit_start=None,
            default_style='', width=8192
        )

    def write_out_lxc_metadata(
        self,
        lxc: models.proxmox.LXC
    ):
        yaml_description = self._serialize_metadata(lxc.metadata)
        
        self.prox.nodes(lxc.node).lxc(f"{lxc.id}/config").put(description=yaml_description)

    def create_lxc(
        self,
        account: models.account.Account,
        hostname: str,
        request_detail: models.proxmox.RequestDetail
    ) -> Tuple[str,str]:
        if request_detail.template_id not in config.proxmox.lxc.templates:
            raise exceptions.resource.Unavailable(f"LXC template {detail.template_id} does not exist!")

        template = config.proxmox.lxc.templates[request_detail.template_id]

        if template.disk_format != models.proxmox.Template.DiskFormat.TarGZ:
            raise exceptions.resource.Unavailable(f"LXC template {detail.template_id} must use TarGZ of RootFS format!")

        try:
            existing_vm = self.read_lxc_by_account(account, hostname)
            raise exceptions.resource.AlreadyExists(f"LXC {hostname} already exists")
        except exceptions.resource.NotFound:
            pass

        node_name = self._select_best_node(template.specs)
        fqdn = self._get_lxc_fqdn_for_account(account, hostname)
        
        lxc_images_path = self.prox.storage(config.proxmox.lxc.dir_pool).get()['path'] + "/template/cache"
        image_path = f"{lxc_images_path}/{template.disk_sha256sum}.{template.disk_format}"
        download_path = f"{lxc_images_path}/{socket.gethostname()}-{os.getpid()}-{template.disk_sha256sum}"

        with ProxmoxNodeSSH(node_name) as con:
            stdin, stdout, stderr = con.ssh.exec_command(
                f"mkdir -p {lxc_images_path}"
            )
            status = stdout.channel.recv_exit_status()

            if status != 0:
                raise exceptions.resource.Unavailable(f"Could not download template: could not reserve download dir")

            # See if the image exists
            try:
                con.sftp.stat(image_path)

                # Checksum image    
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"sha256sum {image_path} | cut -f 1 -d' '"
                )

                if template.disk_sha256sum not in str(stdout.read()):
                    raise exceptions.resource.Unavailable(f"Downloaded template does not pass SHA256SUMS given {status}: {stderr.read()} {stdout.read()}")
            except FileNotFoundError as e:
                # Original image does not exist, we gotta download it
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"wget {template.disk_url} -O {download_path}"
                )
                status = stdout.channel.recv_exit_status()

                if status != 0:
                   raise exceptions.resource.Unavailable(f"Could not download template: error {status}: {stderr.read()} {stdout.read()}")

                # Checksum image    
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"sha256sum {download_path} | cut -f 1 -d' '"
                )

                if template.disk_sha256sum not in str(stdout.read()):
                    raise exceptions.resource.Unavailable(f"Downloaded template does not pass SHA256SUM given {status}: {stderr.read()} {stdout.read()}")

                # Move image
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"rm -f {image_path} && mv {download_path} {image_path}"
                )

                status = stdout.channel.recv_exit_status()
                if status != 0:
                    provision_failed(f"Couldn't rename template {status}: {stderr.read()} {stdout.read()}")

        nic_allocation=models.proxmox.NICAllocation(
            addresses=[
                self._allocate_ip_lxc()
            ],
            gateway4=config.proxmox.lxc.network.ip + 1, # router address is assumed to be .1 of the subnet
            macaddress="02:00:00:%02x:%02x:%02x" % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        )

        user_ssh_public_key, user_ssh_private_key = utilities.auth.generate_rsa_public_private_ssh_key_pair()
        mgmt_ssh_public_key, mgmt_ssh_private_key = utilities.auth.generate_rsa_public_private_ssh_key_pair()
        password = self._random_password()

        metadata = models.proxmox.LXCMetadata(
            owner=account.username,
            request_detail=request_detail,
            inactivity=models.proxmox.Inactivity(
                marked_active_at=datetime.date.today()
            ),
            network=models.proxmox.Network(
                nic_allocation=nic_allocation
            ),
            root_user=models.proxmox.RootUser(
                password_hash=self._hash_password(password),
                ssh_public_key=user_ssh_public_key,
                mgmt_ssh_public_key=mgmt_ssh_public_key,
                mgmt_ssh_private_key=mgmt_ssh_private_key
            )
        )

        # reserve a VM, but don't set any of the specs yet
        # just setup the metadata we'll need later
        random.seed(f"{fqdn}-{node_name}")
        hash_id = random.randint(1000, 5000000)
        random.seed()

        # Store VM metadata in the description field
        # https://github.com/samuelcolvin/pydantic/issues/1043
        yaml_description = self._serialize_metadata(metadata)
        
        result = self.prox.nodes(f"{node_name}/lxc").post(**{
            "hostname": fqdn,
            "vmid": hash_id,
            "description": yaml_description,
            "ostemplate": f"{config.proxmox.lxc.dir_pool}:vztmpl/{template.disk_sha256sum}.{template.disk_format}",
            "cores": template.specs.cores,
            "memory": template.specs.memory,
            "swap": template.specs.swap,
            "storage": config.proxmox.lxc.dir_pool,
            "unprivileged": 1,
            "ssh-public-keys": f"{user_ssh_public_key}\n{mgmt_ssh_public_key}"
        })

        self._wait_vmid_lock(node_name, hash_id)
        
        # if there is an id collision, proxmox will do id+1, so we need to search for the lxc again
        lxc = self._read_lxc_by_fqdn(fqdn)

        self.prox.nodes(lxc.node).lxc(f"{lxc.id}/resize").put(
            disk='rootfs',
            size=f'{template.specs.disk_space}G'
        )

        self._wait_vmid_lock(node_name, lxc.id)

        return password, user_ssh_private_key

    def _wait_vmid_lock(
        self,
        node_name: str,
        vm_id: int,
        timeout: int = 25,
        poll_interval: int = 1
    ):
        """Waits for Proxmox to unlock the VM, it typically locks it when it's resizing a disk/creating a vm/etc..."""
        start = time.time()
        while True:
            res = self.prox.nodes(node_name).lxc(f"{vm_id}/config").get()
            now = time.time()

            if 'lock' not in res: 
                break

            if (now-start) > timeout:
                raise exceptions.resource.Unavailable("Timeout occured waiting for VPS/LXC to unlock.")

            time.sleep(poll_interval)


    def _read_lxc_on_node(
        self,
        node: str,
        id: int
    ) -> models.proxmox.LXC:

        try:
            lxc_config = self.prox.nodes(node).lxc.get(f"{id}/config")
        except Exception as e:
            raise exceptions.resource.NotFound("The VM does not exist")

        # proxmox uses hostname as the lxc name
        # but name for vm name, god help me
        fqdn = lxc_config['hostname']

        # decode description
        try:
            metadata = models.proxmox.LXCMetadata.parse_obj(
                yaml.safe_load(lxc_config['description'])
            )
        except Exception as e:
            raise exceptions.resource.Unavailable(
                f"LXC is unavailable, malformed metadata description: {e}"
            )

        # for user ocanty, returns .ocanty.lxc.cloud.netsoc.co
        suffix = self._get_lxc_fqdn_for_username(metadata.owner, "")

        # trim suffix
        if not fqdn.endswith(suffix):
            raise exceptions.resource.Unavailable(
                f"Found but Owner / FQDN do not align, FQDN is {lxc_fqdn} but owner is {metadata.owner}"
            )

        hostname = fqdn[:-len(suffix)]

        if (datetime.date.today() - metadata.inactivity.marked_active_at).days > config.proxmox.lxc.inactivity_shutdown_num_days:
            active = False
        else:
            active = True 

        # config str looks like this: whatever,size=30G
        # extract the size str
        size_str = dict(map(lambda x: (x.split('=') + [""])[:2], lxc_config['rootfs'].split(',')))['size']

        disk_space = int(size_str[:-1])

        specs = models.proxmox.Specs(
            cores=lxc_config['cores'],
            memory=lxc_config['memory'],
            swap=lxc_config['swap'],
            disk_space=disk_space
        )

        current_status = self.prox.nodes(node).lxc.get(f"{id}/status/current")
        if current_status['status'] == 'running':
            status = models.proxmox.Status.Running
        elif current_status['status'] == 'stopped':
            status = models.proxmox.Status.Stopped

        lxc = models.proxmox.LXC(
            id=id,
            fqdn=fqdn,
            hostname=hostname,
            node=node,
            metadata=metadata,
            specs=specs,
            remarks=[],
            status=status,
            active=active
        )

        # Build remarks about the thing, problems, etc...
        for vhost in lxc.metadata.network.vhosts:
            remarks = self._validate_domain(vhost)

            if remarks is not None:
                lxc.remarks += remarks

        return lxc

    def _read_lxc_by_fqdn(
        self,
        fqdn: str
    ) -> models.proxmox.LXC:
        # Look on each node for the VM
        for node in self.prox.nodes().get():
            for potential_lxc in self.prox.nodes(node['node']).lxc.get():
                # is it an one of our lxc fqdns?
                if potential_lxc['name'] == fqdn:
                    lxc = self._read_lxc_on_node(node['node'], potential_lxc['vmid'])
                    return lxc
        
        raise exceptions.resource.NotFound("The VM does not exist")

    def read_lxc_by_account(
        self,
        account: models.account.Account,
        hostname: str
    ) -> models.proxmox.LXC:
        return self._read_lxc_by_fqdn(self._get_lxc_fqdn_for_account(account, hostname))

    def read_lxcs_by_account(
        self,
        account: models.account.Account
    ) -> Dict[str, models.proxmox.LXC]:
        """Returns a dict indexed by hostname of uservms owned by user account"""

        ret = { }
        
        for node in self.prox.nodes().get():
            for lxc_dict in self.prox.nodes(node['node']).lxc.get():
                if lxc_dict['name'].endswith(self._get_lxc_fqdn_for_account(account, "")):
                    lxc = self._read_lxc_on_node(node['node'], lxc_dict['vmid'])
                    ret[lxc.hostname] = lxc
                    
        
        return ret

    def read_lxcs(
        self
    ) -> Dict[str, models.proxmox.LXC]:
        ret = {}

        for node in self.prox.nodes().get():
            for lxc_dict in self.prox.nodes(node['node']).lxc.get():
                if lxc_dict['name'].endswith(config.proxmox.lxc.base_fqdn):
                    lxc = self._read_lxc_on_node(node['node'], lxc_dict['vmid'])
                    ret[lxc.fqdn] = lxc

        return ret  

    def reset_root_user_lxc(
        self,
        lxc: models.proxmox.LXC
    ) -> Tuple[str, str]:
        """Returns a tuple of password, private_key"""

        if lxc.status == models.proxmox.Status.Stopped:
            raise exceptions.resource.Unavailable("The LXC must be running to reset the root password")

        user_ssh_public_key, user_ssh_private_key = utilities.auth.generate_rsa_public_private_ssh_key_pair()
        mgmt_ssh_public_key, mgmt_ssh_private_key = utilities.auth.generate_rsa_public_private_ssh_key_pair()

        password = self._random_password()

        lxc.metadata.root_user = models.proxmox.RootUser(
            password_hash=self._hash_password(password),
            ssh_public_key=user_ssh_public_key,
            mgmt_ssh_public_key=mgmt_ssh_public_key,
            mgmt_ssh_private_key=mgmt_ssh_private_key
        )
        lxc.metadata.apply_root_reset_on_next_boot = True
        self.write_out_lxc_metadata(lxc)

        with ProxmoxNodeSSH(lxc.node) as con:
            escaped_hash = lxc.metadata.root_user.password_hash.replace('$','$')
            stdin, stdout, stderr = con.ssh.exec_command(
                f"echo -e 'root:{escaped_hash}' | pct exec {lxc.id} -- chpasswd -e"
            )
            status = stdout.channel.recv_exit_status()

            logger.info(stdout.read()) 
            logger.info(stderr.read())

            if status != 0:
                raise exceptions.resource.Unavailable(
                    f"Could not start LXC: unable to set root password: {status}: {stdout.read()} {stderr.read()}"
                )

            stdin, stdout, stderr = con.ssh.exec_command(
                f"echo -e '# --- BEGIN PVE ---\\n{lxc.metadata.root_user.ssh_public_key}\\n{lxc.metadata.root_user.mgmt_ssh_public_key}\\n# --- END PVE ---' | pct push { lxc.id } /dev/stdin '/root/.ssh/authorized_keys' --perms 0600 --user 0 --group 0"
            )
            status = stdout.channel.recv_exit_status()

            if status != 0:
                raise exceptions.resource.Unavailable(
                    f"Could not start LXC: unable to inject ssh keys {status}: {stdout.read()} {stderr.read()}"
                )

        return password, user_ssh_private_key

    def start_lxc(
        self,
        lxc: models.proxmox.LXC
    ):
        if lxc.status != models.proxmox.Status.Running:
            logger.info(f"rate=100,name=eth0,bridge={config.proxmox.lxc.bridge},tag={config.proxmox.lxc.vlan},hwaddr={lxc.metadata.network.nic_allocation.macaddress},ip={lxc.metadata.network.nic_allocation.addresses[0]},mtu=1450")

            self.prox.nodes(lxc.node).lxc(f"{lxc.id}/config").put(**{
                "nameserver": "1.1.1.1",
                "net0": f"rate=100,name=eth0,bridge={config.proxmox.lxc.bridge},tag={config.proxmox.lxc.vlan},hwaddr={lxc.metadata.network.nic_allocation.macaddress},ip={lxc.metadata.network.nic_allocation.addresses[0]},mtu=1450",
            })

            self.prox.nodes(lxc.node).lxc(f"{lxc.id}/status/start").post()

    def stop_lxc(
        self,
        lxc: models.proxmox.LXC
    ):
        if lxc.status == models.proxmox.Status.Running:
            self.prox.nodes(lxc.node).lxc(f"{lxc.id}/status/stop").post()

    def shutdown_lxc(
        self,
        lxc: models.proxmox.LXC
    ):
        if lxc.status == models.proxmox.Status.Running:
            self.prox.nodes(lxc.node).lxc(f"{lxc.id}/status/shutdown").post()

    def mark_active_lxc(
        self,
        lxc: models.proxmox.LXC
    ): 
        # reset inactivity status, this resets tracking of the emails too
        lxc.metadata.inactivity = models.proxmox.Inactivity(
            marked_active_at = datetime.date.today()
        )
        self.write_out_lxc_metadata(lxc)

    def add_vhost_lxc(
        self,
        lxc: models.proxmox.LXC,
        vhost: str
    ):
        lxc.metadata.network.vhosts.add(vhost)
        self.write_out_lxc_metadata(lxc)

    def remove_vhost_lxc(
        self,
        lxc: models.proxmox.LXC,
        vhost: str
    ):
        if vhost in lxc.metadata.network.vhosts:
            lxc.metadata.network.vhosts.remove(vhost)

            self.write_out_lxc_metadata(lxc)
        else:
            raise exceptions.resource.NotFound(f"Could not find {vhost} on resource")

    def get_port_forward_map(
        self
    ) -> Dict[int,Tuple[ipaddress.IPv4Interface, int]]:
        lxcs = self.read_lxcs()

        port_map = {}

        for fqdn, lxc in lxcs:
            ip = lxc.metadata.network.nic_allocation.addresses[0]

            for external_port, internal_port in lxc.metadata.network.ports:
                if external_port in port_map:
                    logger.warning(f"warning, conflicting port map: {lxc.fqdn} tried to map {external_port} but it's already taken!")
                    continue

                if config.proxmox.port_forward.range[0] > external_port or external_port > config.proxmox.port_forward.range[1]:
                    logger.warning(f"warning, port out of range: {lxc.fqdn} tried to map {external_port} but it's out of range!")
                    continue
                
                port_map[external_port] = (ip, internal_port)
        
        return port_map

    def _validate_domain(
        self,
        username: models.account.Username,
        domain: str
    ) -> Optional[List[str]]:
        """
        Verifies a single domain, if the domain is valid, None is returned
        If the domain is invalid, a list of remarks is returned
        """
        return None

        # txt_name = config.proxmox.user_domains.user_supplied.verification_txt_name
        # txt_content = username

        # base_domain = config.proxmox.user_domains.netsoc_supplied.base_domain
        # allowed_a_aaaa = config.proxmox.user_domains.user_supplied.allowed_a_aaaa

        # split_domain = domain.split(".")

        # remarks = []
            
        # # *.netsoc.co etc
        # if domain.endswith(f".{base_domain}"):
        #     # the stuff at the start, i.e if they specified blog.ocanty.netsoc.co
        #     # prefix is blog.ocanty
        #     prefix = domain[:-len(f".{base_domain}")]
        #     split_prefix = prefix.split(".")
            
        #     # extract last part, i.e blog.ocanty => ocanty
        #     if split_prefix[-1] == user:
        #         # Valid domain
        #         return None
        #     else:
        #         remarks.append(f"Domain {domain} - subdomain {split_prefix[:len(split_prefix)-1]} must end with one of {username}.{base_domain}")
        # else: # custom domain
        #     try:
        #         info_list = socket.getaddrinfo(domain, 80)
        #     except Exception as e:
        #         remarks.append("Could not verify custom domain: {e}")

        #     a_aaaa = set(map(lambda info: info[4][0], filter(lambda x: x[0] in [socket.AddressFamily.AF_INET, socket.AddressFamily.AF_INET6], info_list)))
            
        #     if len(a_aaaa) == 0:
        #         remarks.append(f"Domain {domain} - no A or AAAA records present")

        #     for record in a_aaaa:
        #         if record not in allowed_a_aaaa:
        #             remarks.append(f"Domain {domain} - unknown A/AAAA record on domain ({record}), must be one of {allowed_a_aaaa}")

        #     # we need to check if they have the appropiate TXT record with the correct value
        #     custom_base = f"{split[len(split)-2]}.{split[len(split)-1]}"

        #     # check for _netsoc.theirdomain.com 
        #     try:
        #         q = dns.resolver.resolve(f"{txt_name}.{custom_base}", 'TXT')

        #         # dnspython returns the TXT record value enclosed in quotation marks
        #         # we will need to remove these
        #         txt_res = set(map(lambda x: str(x).strip('"'),q))

        #         if txt_content not in txt_res:
        #             remarks.append(f"Host {domain} - could not find TXT record {txt_name} ({txt_name}.{custom_base}) set to {txt_content}, instead found {txt_res}!")
        #     except dns.resolver.NXDOMAIN:
        #         remarks.append(f"Host {domain} - could not find TXT record {txt_name} ({txt_name}.{custom_base}) set to {txt_content}")
        #     except dns.exception.DNSException as e:
        #         remarks.append(f"Host {domain} - unable to lookup record ({txt_name}.{custom_base}): ({e})")
        #     except Exception as e:
        #         remarks.append(f"Host {domain} - error {e} (contact SysAdmins)")

        # return remarks

    def get_vhost_forward_map(
        self
    ) -> Dict[str, ipaddress.IPv4Address]:
        vhost_map = {}

        for fqdn, lxc in lxcs:
            ip = lxc.metadata.network.nic_allocation.addresses[0]

            for domain in lxc.metadata.network.vhosts:
                logger.warning(f"warning, conflicting port map: {lxc.fqdn} tried to map {external_port} but it's already taken!")

        return port_map

    def add_port_lxc(
        self,
        lxc: models.proxmox.LXC,
        external: int,
        internal: int
    ):
        port_map = self.get_port_forward_map()

        if external in port_map:
            raise exceptions.resource.Unavailable("Cannot map port {external}, this port is currently taken by another user/another one of your VMs/LXCs")
            
        lxc.metadata.network.ports[external] = internal

    def remove_port_lxc(
        self, 
        vm: models.proxmox.LXC,
        external: int
    ):
        if external in lxc.metadata.network.ports:
            del lxc.metadata.network.ports[external]


    def _get_vps_fqdn_for_username(
        self,
        username: str,
        hostname: str
    ) -> str:
        return f"{hostname}.{username}.{config.proxmox.vps.base_fqdn}"

    def _get_vps_fqdn_for_account(
        self,
        account: models.account.Account,
        hostname: str
    ) -> str:
        """
        Returns a FQDN for a VM hostname for an account

        i.e cake => cake.ocanty.uservm.netsoc.co
        """
        return self._get_vps_fqdn_for_username(account.username, hostname)

#     def _read_uservm_on_node(
#         self,
#         node: str,
#         fqdn: str
#     ) -> models.proxmox.UserVM:  
#         """Find a VM on a node or throw an exception"""

#         # get each vm on the node
#         for vm_dict in self.prox.nodes(node).qemu.get():
#             if vm_dict['name'] == fqdn:
#                 vm_config = self.prox.nodes(node).qemu.get(f"{vm_dict['vmid']}/config")

#                 # decode description
#                 try:
#                     metadata = models.proxmox.Metadata.parse_obj(
#                         yaml.safe_load(vm_config['description'])
#                     )
#                 except Exception as e:
#                     raise exceptions.resource.Unavailable(
#                         f"User VM is unavailable, malformed metadata description: {e}"
#                     )

#                 # for user ocanty, returns .ocanty.uservm.netsoc.co
#                 suffix = self._get_uservm_fqdn_for_username(metadata.owner, "")

#                 # trim suffix
#                 if not vm_dict['name'].endswith(suffix):
#                     raise exceptions.resource.Unavailable(
#                         f"Found VM but Owner / FQDN do not align, FQDN is {vm_dict['name']} but owner is {metadata.owner}"
#                     )

#                 hostname = vm_dict['name'][:-len(suffix)]


#                 if (datetime.date.today() - metadata.inactivity.marked_active_at).days > config.proxmox.uservm.inactivity_shutdown_num_days:
#                     active = False
#                 else:
#                     active = True 

#                 vm = models.proxmox.UserVM(
#                     id=vm_dict['vmid'],
#                     fqdn=fqdn,
#                     hostname=hostname,
#                     node=node,
#                     metadata=metadata,
#                     specs=metadata.provision.image.specs,
#                     remarks=[],
#                     status=models.proxmox.Status.NotApplicable,
#                     active=active
#                 )

#                 # if it's a vm request
#                 if metadata.provision.stage == models.proxmox.Provision.Stage.AwaitingApproval:
#                     vm.remarks.append(
#                         "Your VM is currently awaiting approval from the SysAdmins, you will receive an email once it has been approved"
#                     )
#                 elif metadata.provision.stage == models.proxmox.Provision.Stage.Approved:
#                     vm.remarks.append(
#                         "Your VM has been approved, you can now flash it's image"
#                     )
#                 elif metadata.provision.stage == models.proxmox.Provision.Stage.Installed:
#                     disk_space = 0

#                     if 'virtio0' not in vm_config:
#                         vm.remarks.append("VM is missing its disk. Contact SysAdmins")
#                     else:
#                         # config str looks like this: local-lvm:vm-1867516-disk-0,backup=0,size=30G

#                         # extract the size str
#                         size_str = dict(map(lambda x: (x.split('=') + [""])[:2], vm_config['virtio0'].split(',')))['size']

#                         disk_space = int(size_str[:-1])

#                     vm.specs=models.proxmox.Specs(
#                         cores=vm_config['cores'],
#                         memory=vm_config['memory'],
#                         disk_space=0
#                     )
#                 else:
#                     vm.remarks.append(
#                         "Installation may take awhile, check back later"
#                     )

#                 vm_current_status = self.prox.nodes(node).qemu.get(f"{vm_dict['vmid']}/status/current")
#                 logger.info(vm_current_status)
#                 if vm_current_status['status'] == 'running':
#                     vm.status = models.proxmox.Status.Running
#                 elif vm_current_status['status'] == 'stopped':
#                     vm.status = models.proxmox.Status.Stopped

#                 return vm

#         raise exceptions.resource.NotFound("The VM does not exist")


#     def _read_uservm_by_fqdn(
#         self,
#         fqdn: str
#     ) -> models.proxmox.UserVM:
#         """Find a VM in the cluster or throw an exception"""

#         # Look on each node for the VM
#         for node in self.prox.nodes().get():
#             try:
#                 vm = self._read_uservm_on_node(node['node'], fqdn)
#                 return vm
#             except exceptions.resource.NotFound:
#                 pass
        
#         raise exceptions.resource.NotFound("The VM does not exist")

#     def read_uservm_by_account(
#         self,
#         account: models.account.Account,
#         hostname: str
#     ) -> models.proxmox.UserVM:
#         """Read a VM owned by an account"""
#         return self._read_uservm_by_fqdn(self._get_uservm_fqdn_for_account(account, hostname))

#     def read_uservms_by_account(
#         self,
#         account: models.account.Account
#     ) -> Dict[str, models.proxmox.UserVM]:
#         """Returns a dict indexed by hostname of uservms owned by user account"""

#         ret = { }
        
#         for node in self.prox.nodes().get():
#             for vm in self.prox.nodes(node['node']).qemu.get():
#                 if vm['name'].endswith(config.proxmox.uservm.base_fqdn):
#                     try:
#                         vm = self._read_uservm_on_node(node['node'], fqdn)
                        
#                         if vm.owner == account.username:
#                             ret[vm.hostname] = vm

#                     except Exception as e:
#                         pass
        
#         return ret

#     def read_uservms(
#         self
#     ) -> Dict[str, models.proxmox.UserVM]:
#         """Returns a dict of all user vms indexed by fqdn"""
#         ret = { }
        
#         for node in self.prox.nodes().get():
#             for vm in self.prox.nodes(node['node']).qemu.get():
#                 if vm['name'].endswith(config.proxmox.uservm.base_fqdn):
#                     try:
#                         vm = self._read_uservm_on_node(node['node'], fqdn)
                        
#                         ret[vm.fqdn] = vm

#                     except Exception as e:
#                         pass

#         return ret

#     def reset_root_password_ssh_key_uservm(
#         self,
#         vm: models.proxmox.UserVM
#     ) -> Tuple[str, str]:
#         """
#         Reset the root password, ssh key on a VM
#         Returns a tuple with password and private key
#         """
#         was_running = False

#         if vm.status == models.proxmox.Status.Running:
#             self.stop_uservm(vm)
#             was_running = True
        
#         password = self._random_password()
        
#         public_key, private_key = utilities.auth.generate_rsa_public_private_key_pair()

#         vm.metadata.root_user.password_hash = self._hash_password(password)
#         vm.metadata.root_user.ssh_public_key = public_key
#         vm.metadata.reapply_cloudinit_on_next_boot = True

#         self.write_out_uservm_metadata(vm)

#         if was_running:
#             self.start_uservm(vm)

#         return password, private_key

#     def request_userlxc(
#         self,
#         account: models.account.Account,
#         hostname: str,
#         image: models.proxmox.Im
#     ):
#         pass

#     def request_uservm(
#         self,
#         account: models.account.Account,
#         hostname: str,
#         image: models.proxmox.Image,
#         reason: str
#     ):
#         try:
#             existing_vm = self.read_uservm_by_account(account, hostname)
#             raise exceptions.resource.AlreadyExists(f"VM {hostname} already exists")
#         except exceptions.resource.NotFound as e:
#             pass

#         node_name = self._select_best_node(image.specs)
#         fqdn = self._get_uservm_fqdn_for_account(account, hostname)
#         # Allocate the VM on an IP address that is not the gateway, network or broadcast address
#         # TODO - don't use random
#         offset_ip = (config.proxmox.uservm.network.ip + 1) + random.randint(1,config.proxmox.uservm.network.network.num_addresses-3)
#         assigned_ip_and_netmask = f"{offset_ip}/{config.proxmox.uservm.network.network.prefixlen}"

#         nic_allocation=models.proxmox.NICAllocation(
#             addresses=[
#                 ipaddress.IPv4Interface(assigned_ip_and_netmask)
#             ],
#             gateway4=config.proxmox.uservm.network.ip + 1, # router address is assumed to be .1 of the subnet
#             macaddress="02:00:00:%02x:%02x:%02x" % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
#         )

#         user_public_key, user_private_key = utilities.auth.generate_rsa_public_private_key_pair()
#         mgmt_public_key, mgmt_private_key = utilities.auth.generate_rsa_public_private_key_pair()

#         metadata = models.proxmox.Metadata(
#             owner=account.username,
#             provision=models.proxmox.Provision(
#                 image=image
#             ),
#             reason=reason,
#             inactivity=models.proxmox.Inactivity(
#                 requested_at=datetime.date.today(),
#                 marked_active_at=datetime.date.today()
#             ),
#             network=models.proxmox.Network(
#                 ports=[],
#                 domains=[],
#                 nic_allocation=nic_allocation
#             ),
#             root_user=models.proxmox.RootUser(
#                 password_hash=self._hash_password(self._random_password()),
#                 ssh_public_key=user_public_key,
#                 mgmt_ssh_public_key=mgmt_public_key,
#                 mgmt_ssh_private_key=mgmt_private_key
#             )
#         )

#         # reserve a VM, but don't set any of the specs yet
#         # just setup the metadata we'll need later
#         random.seed(f"{fqdn}-{node_name}")
#         vm_hash_id = random.randint(1000, 5000000)
#         random.seed()

#         # Store VM metadata in the description field
#         # https://github.com/samuelcolvin/pydantic/issues/1043
#         yaml_description = self._serialize_uservm_metadata(metadata)
        
#         self.prox.nodes(f"{node_name}/qemu").post(
#             name=fqdn,
#             vmid=vm_hash_id,
#             description=yaml_description
#         )

#     def _serialize_uservm_metadata(
#         self,
#         metadata: models.proxmox.Metadata
#     ) -> str:
#         return yaml.safe_dump(
#             yaml.safe_load(metadata.json()),
#             default_flow_style=False,
#             explicit_start=None,
#             default_style='', width=8192
#         )

#     def write_out_uservm_metadata(
#         self,
#         vm: models.proxmox.UserVM
#     ):
#         yaml_description = self._serialize_uservm_metadata(vm.metadata)
        
#         # https://github.com/samuelcolvin/pydantic/issues/1043
#         self.prox.nodes(vm.node).qemu(f"{vm.id}/config").post(description=yaml_description)

#     def approve_uservm(
#         self,
#         vm: models.proxmox.UserVM
#     ):  
#         if vm.metadata.suspension.status is True:
#             raise exceptions.resource.Unavailable("Cannot perform this action on a suspended VM")

#         if vm.metadata.provision.stage == models.proxmox.Provision.Stage.AwaitingApproval:
#             vm.metadata.provision.stage = models.proxmox.Provision.Stage.Approved
#             self.write_out_uservm_metadata(vm)

#             self.mark_active_uservm(vm)
    
#     def mark_active_uservm(
#         self,
#         vm: models.proxmox.UserVM
#     ): 
#         # reset inactivity status
#         vm.metadata.inactivity = models.proxmox.Inactivity(
#             marked_active_at = datetime.date.today()
#         )
#         self.write_out_uservm_metadata(vm)

#     def flash_uservm_image(
#         self,
#         vm: models.proxmox.UserVM
#     ):
#         if vm.metadata.provision.stage == models.proxmox.Provision.Stage.AwaitingApproval:
#             raise exceptions.resource.Unavailable("Cannot flash VM. VM is currently awaiting approval Check your email")

#         if vm.metadata.suspension.status is True:   
#             raise exceptions.resource.Unavailable("Cannot flash VM. VM is suspended for ToS violation!")

#         if vm.status == models.proxmox.Status.Running:
#             raise exceptions.resource.Unavailable("Cannot flash VM. VM is running! Stop VM and try again")

        
#         # if vm.metadata.provision.stage == models.proxmox.Provision.Stage.Failed:
#         #     raise exceptions.resource.Unavailable("Cannot install VM. Uninstall VM ")

#         # # Approved is the base "approved but not installed" state
#         # if vm.metadata.provision.stage != models.proxmox.Provision.Stage.Approved or :
#         #     raise exceptions.resource.Unavailable("VM is currently installing/already installed")

#         def provision_stage(stage: models.proxmox.Provision.Stage):
#             vm.metadata.provision.stage = stage
#             vm.metadata.provision.remarks = []
#             self.write_out_uservm_metadata(vm)

#         def provision_remark(line: str):
#             vm.metadata.provision.remarks.append(line)
#             self.write_out_uservm_metadata(vm)

#         def provision_failed(reason: str):
#             provision_stage(models.proxmox.Provision.Stage.Failed)
#             provision_remark(reason)
#             self.write_out_uservm_metadata(vm)

#             raise exceptions.resource.Unavailable(f"VM {vm.hostname} installation failed, check remarks")

#         provision_stage(models.proxmox.Provision.Stage.Began)
        
#         images_path = f"/tmp/admin-api/"
#         image_path = f"/tmp/admin-api/{vm.metadata.provision.image.disk_sha256sum}"
#         download_path = f"{images_path}/{socket.gethostname()}-{os.getpid()}-{vm.metadata.provision.image.disk_sha256sum}"

#         with ProxmoxNodeSSH(vm.node) as con:
#             stdin, stdout, stderr = con.ssh.exec_command(
#                 f"mkdir -p {images_path}"
#             )
#             status = stdout.channel.recv_exit_status()

#             if status != 0:
#                 provision_failed(f"Could not download image: could not reserve download dir")

#             # See if the image exists
#             try:
#                 con.sftp.stat(image_path)

#                 # Checksum image    
#                 stdin, stdout, stderr = con.ssh.exec_command(
#                     f"sha256sum {image_path} | cut -f 1 -d' '"
#                 )

#                 if vm.metadata.provision.image.disk_sha256sum not in str(stdout.read()):
#                     provision_failed(f"Downloaded image does not pass SHA256SUMS given {status}: {stderr.read()} {stdout.read()}")

#             except FileNotFoundError as e:
#                 provision_stage(models.proxmox.Provision.Stage.DownloadImage)

#                 # Original image does not exist, we gotta download it
#                 stdin, stdout, stderr = con.ssh.exec_command(
#                     f"wget {vm.metadata.provision.image.disk_url} -O {download_path}"
#                 )
#                 status = stdout.channel.recv_exit_status()

#                 if status != 0:
#                     provision_failed(f"Could not download image: error {status}: {stderr.read()} {stdout.read()}")

#                 # Checksum image    
#                 stdin, stdout, stderr = con.ssh.exec_command(
#                     f"sha256sum {download_path} | cut -f 1 -d' '"
#                 )

#                 if vm.metadata.provision.image.disk_sha256sum not in str(stdout.read()):
#                     provision_failed(f"Downloaded image does not pass SHA256SUM given {status}: {stderr.read()} {stdout.read()}")

#                 # Move image
#                 stdin, stdout, stderr = con.ssh.exec_command(
#                     f"rm -rf {image_path} && mv {download_path} {image_path}"
#                 )

#                 status = stdout.channel.recv_exit_status()
#                 if status != 0:
#                     provision_failed(f"Couldn't rename VM image {status}: {stderr.read()} {stdout.read()}")
            
#             provision_stage(models.proxmox.Provision.Stage.FlashImage)

#             # Images path for installed VMs
#             vms_images_path = self.prox.storage(config.proxmox.uservm.dir_pool).get()['path'] + "/images"

#             # Move disk image
#             stdin, stdout, stderr = con.ssh.exec_command(
#                 f"cd {vms_images_path} && rm -rf {vm.id} && mkdir {vm.id} && cd {vm.id} && cp {image_path} ./primary.{ vm.metadata.provision.image.disk_format }"
#             )
#             status = stdout.channel.recv_exit_status()
            
#             if status != 0:
#                 provision_failed(f"Couldn't copy VM image {status}: {stderr.read()} {stdout.read()}")

#             # Create disk for EFI
#             stdin, stdout, stderr = con.ssh.exec_command(
#                 f"cd {vms_images_path}/{vm.id} && qemu-img create -f qcow2 efi.qcow2 128K"
#             )
#             status = stdout.channel.recv_exit_status()
            
#             if status != 0:
#                 provision_failed(f"Couldn't create EFI image {status}: {stderr.read()} {stdout.read()}")

#             provision_stage(models.proxmox.Provision.Stage.SetSpecs)

#             self.prox.nodes(vm.node).qemu(f"{vm.id}/config").put(
#                 virtio0=f"{config.proxmox.uservm.dir_pool}:{vm.id}/primary.{ vm.metadata.provision.image.disk_format }",
#                 cores=vm.metadata.provision.image.specs.cores,
#                 memory=vm.metadata.provision.image.specs.memory,
#                 bios='ovmf',
#                 efidisk0=f"{config.proxmox.uservm.dir_pool}:{vm.id}/efi.qcow2",
#                 scsihw='virtio-scsi-pci',
#                 machine='q35',
#                 serial0='socket',
#                 bootdisk='virtio0'
#             )

#             self.prox.nodes(vm.node).qemu(f"{vm.id}/resize").put(
#                 disk='virtio0',
#                 size=f'{vm.metadata.provision.image.specs.disk_space}G'
#             )

#             provision_stage(models.proxmox.Provision.Stage.Installed)

#     def start_uservm(
#         self,
#         vm : models.proxmox.UserVM
#     ):
#         if vm.metadata.suspension.status is True:
#             raise exceptions.resource.Unavailable("Cannot perform this action on a suspended VM")

#         if vm.metadata.provision.stage != models.proxmox.Provision.Stage.Installed:
#             raise exceptions.resource.Unavailable("Cannot start a VM that is not marked as installed!")

#         # Detach existing cloud-init drive (if any)
#         self.prox.nodes(vm.node).qemu(f"{vm.id}/config").put(
#             ide2="none,media=cdrom",
#             cicustom=""
#         )

#         # install cloud-init data
#         with ProxmoxNodeSSH(vm.node) as con:
#             snippets_path = self.prox.storage(config.proxmox.uservm.dir_pool).get()['path'] + "/snippets"

#             con.sftp.putfo(
#                 io.StringIO(""),
#                 f'{ snippets_path }/{vm.fqdn}.metadata.yml'
#             )

#             userdata_config = f"""#cloud-config
# preserve_hostname: false
# manage_etc_hosts: true
# fqdn: { vm.fqdn }
# ssh_pwauth: 1
# disable_root: 0
# packages:
#     - qemu-guest-agent
# runcmd:
#     - [ systemctl, enable, qemu-guest-agent ]
#     - [ systemctl, start, qemu-guest-agent, --no-block ]  
# users:
#     -   name: root
#         lock_passwd: false
#         shell: /bin/bash
#         ssh_redirect_user: false
#         ssh_authorized_keys:
#             - { vm.metadata.root_user.ssh_public_key }
#             - { vm.metadata.root_user.mgmt_ssh_public_key }
# chpasswd:
#     list: |
#         root:{ vm.metadata.root_user.password_hash }
#     expire: false
# """

#             if vm.metadata.reapply_cloudinit_on_next_boot == True:
#                 # This will wipe previous cloud-init state from previous boots
#                 userdata_config += """
# bootcmd: 
#     - rm -f /etc/netplan/50-cloud-init.yml
#     - cloud-init clean --logs
# """         

#             con.sftp.putfo(
#                 io.StringIO(userdata_config),
#                 f'{ snippets_path }/{vm.fqdn}.userdata.yml'
#             )

#             con.sftp.putfo(
#                 io.StringIO(f"""
# ethernets:
#     net0:
#         match:
#             macaddress: { vm.metadata.network.nic_allocation.macaddress }
#         nameservers:
#             search:
#                 - { config.proxmox.uservm.base_fqdn }
#             addresses:
#                 - 1.1.1.1
#                 - 8.8.8.8
#         gateway4: { config.proxmox.uservm.network.ip + 1 }
#         optional: true
#         addresses:
#             - { vm.metadata.network.nic_allocation.addresses[0] }
#         mtu: 1450 
# version: 2
#                 """),
#                 f'{ snippets_path }/{vm.fqdn}.networkconfig.yml'
#             )

#             # Insert cloud-init stuff
#             self.prox.nodes(vm.node).qemu(f"{vm.id}/config").put(
#                 cicustom=f"user={ config.proxmox.uservm.dir_pool }:snippets/{vm.fqdn}.userdata.yml,network={ config.proxmox.uservm.dir_pool }:snippets/{vm.fqdn}.networkconfig.yml,meta={ config.proxmox.uservm.dir_pool }:snippets/{vm.fqdn}.metadata.yml",
#                 ide2=f"{ config.proxmox.uservm.dir_pool }:cloudinit,format=qcow2"
#             )

#             # Set network card
#             self.prox.nodes(vm.node).qemu(f"{vm.id}/config").put(
#                 net0=f"virtio={ vm.metadata.network.nic_allocation.macaddress },bridge=vmbr0,tag=69"
#             )

#             self.prox.nodes(vm.node).qemu(f"{vm.id}/status/start").post()

#             # Reset cloudinit status
#             vm.metadata.reapply_cloudinit_on_next_boot = False
#             self.write_out_uservm_metadata(vm)

#     def delete_uservm(
#         self,
#         vm: models.proxmox.UserVM
#     ):
#         # delete cloudinit
#         with ProxmoxNodeSSH(vm.node) as con:
#             snippets_path = self.prox.storage(config.proxmox.uservm.dir_pool).get()['path'] + "/snippets"

#             stdin, stdout, stderr = con.ssh.exec_command(
#                 f"rm -f '{ snippets_path }/{vm.fqdn}.networkconfig.yml' '{ snippets_path }/{vm.fqdn}.userdata.yml' '{ snippets_path }/{vm.fqdn}.metadata.yml'"
#             )

#         # delete node on proxmox
#         self.prox.nodes(vm.node).qemu(vm.id).delete()


#     def stop_uservm(
#         self,
#         vm : models.proxmox.UserVM
#     ):
#         if vm.metadata.suspension.status is True:
#             raise exceptions.resource.Unavailable("Cannot perform this action on a suspended VM")

#         if vm.metadata.provision.stage != models.proxmox.Provision.Stage.Installed:
#             raise exceptions.resource.Unavailable("VM is not installed")
        
#         self.prox.nodes(vm.node).qemu(f"{vm.id}/config").put(
#             cicustom=''
#         )

#         self.prox.nodes(vm.node).qemu(f"{vm.id}/status/stop").post()

#     def shutdown_uservm(
#         self,
#         vm: models.proxmox.UserVM
#     ):
#         if vm.metadata.suspension.status is True:
#             raise exceptions.resource.Unavailable("Cannot perform this action on a suspended VM")

#         if vm.metadata.provision.stage != models.proxmox.Provision.Stage.Installed:
#             raise exceptions.resource.Unavailable("Cannot shutdown a VM that is not marked as installed!")

#         self.prox.nodes(vm.node).qemu(f"{vm.id}/config").put(
#             cicustom=''
#         )

#         self.prox.nodes(vm.node).qemu(f"{vm.id}/status/shutdown").post()

#     def suspend_uservm(
#         self,
#         vm: models.proxmox.UserVM,
#         suspension: models.proxmox.Suspension
#     ):
#         """Update suspension status"""
#         if vm.status == models.proxmox.Status.Running:
#             self.shutdown_uservm(vm)

#         vm.metadata.suspension = suspension
#         self.write_out_uservm_metadata(vm)


#     def add_domain_uservm(
#         self,
#         vm: models.proxmox.UserVM,
#         domain: str
#     ):
#         vm.metadata.network.domains.add(domain)
#         self.write_out_uservm_metadata(vm)

#     def remove_domain_uservm(
#         self,
#         vm: models.proxmox.UserVM,
#         domain: str
#     ):
#         if domain in vm.metadata.network.domains:
#             vm.metadata.network.domains.remove(domain)

#             self.write_out_uservm_metadata(vm)

#     # def build_exposed_ports_map(
#     #     self
#     # ) -> Dict[int, Tuple[ipaddress.IPv4Address, int]]:
#     #     for self.read_uservms()

#     # def add_port_mapping_uservm(
#     #     self,
#     #     vm: models.proxmox.UserVM,
#     #     mapping: models.proxmox.ExposedPort
#     # ):
#     #     pass

#     # def remove_port_mapping_uservm(
#     #     self, 
#     #     vm: models.proxmox.UserVM,
#     #     mapping: models.proxmox.PortMapping
#     # ):
#     #     pass
        