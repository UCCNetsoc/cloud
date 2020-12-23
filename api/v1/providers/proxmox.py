
import random
import yaml
import datetime
import base64
import requests
import hashlib
import pathlib
import os
import socket
import shutil
import paramiko
import dns
import dns.resolver
import dns.exception
import ipaddress
import io
import re
import crypt
import functools
import string
import time
import selectors

import structlog as logging

from urllib.parse import urlparse, unquote

from typing import Optional, Tuple, List, Dict, Union, Generator
from proxmoxer import ProxmoxAPI

from v1 import models, exceptions, utilities, templates
from v1.config import config

logger = logging.getLogger(__name__)

class ClusterNodeSSH:
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
            hostname=config.proxmox.cluster.ssh.server,
            username=config.proxmox.cluster.ssh.username,
            password=config.proxmox.cluster.ssh.password,
            port=config.proxmox.cluster.ssh.port
        )

        self.jump_transport = self.jump.get_transport()
        self.jump_channel = self.jump_transport.open_channel("direct-tcpip", (self.node_name, 22), ("0.0.0.0", 22))

        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(
            self.node_name, # nodes should be setup in /etc/hosts correctly
            username=config.proxmox.cluster.ssh.username,
            password=config.proxmox.cluster.ssh.password,
            port=22,
            sock=self.jump_channel
        )

        self.sftp = self.ssh.open_sftp()

        return self

    def __exit__(self, type, value, traceback):
        self.sftp.close()
        self.ssh.close()
        self.jump.close()

# Here for historical reasons
# class InstanceSSH:
#     """Paramiko SSH client that will first SSH into an exposed jump host, then jump into any of the Cloud instance"""

#     jump: paramiko.SSHClient
#     ssh: paramiko.SSHClient
    
#     ssh: paramiko.SSHClient
#     sftp: paramiko.SFTPClient
#     instance: models.proxmox.Instance
#     _usernames: Dict[int, str]
#     _groupnames: Dict[int, str]
#     _uids: Dict[str, int]
#     _gids: Dict[str, int]

#     def __init__(self, instance: models.proxmox.Instance):
#         self.jump = paramiko.SSHClient()
#         self.ssh = paramiko.SSHClient()
#         self.instance = instance
#         self._uids = {}
#         self._gids = {}
#         self._usernames = {}
#         self._groupnames = {}
        
#         if instance.status == models.proxmox.Status.Stopped:
#             raise exceptions.resource.Unavailable("Cannot connect to instance. Instance is stopped")

#     def __enter__(self):
#         self.jump.set_missing_host_key_policy(paramiko.AutoAddPolicy())

#         if config.proxmox.network.vlan_jumphost.password is not None:
#             self.jump.connect(
#                 hostname=config.proxmox.network.vlan_jumphost.server,
#                 username=config.proxmox.network.vlan_jumphost.username,
#                 password=config.proxmox.cluster.ssh.password,
#                 port=config.proxmox.network.vlan_jumphost.port
#             )
#         elif config.proxmox.network.vlan_jumphost.private_key is not None:
#             self.jump.connect(
#                 hostname=config.proxmox.network.vlan_jumphost.server,
#                 username=config.proxmox.network.vlan_jumphost.username,
#                 pkey=paramiko.RSAKey.from_private_key(io.StringIO(config.proxmox.network.vlan_jumphost.private_key)),
#                 port=config.proxmox.network.vlan_jumphost.port
#             )
#         else:
#             logger.error("No private key/password for cloud vlan jumphost specified")
            

#         self.jump_transport = self.jump.get_transport()
#         ip = str(self.instance.metadata.network.nic_allocation.addresses[0].ip)

#         self.jump_channel = self.jump_transport.open_channel("direct-tcpip", (ip, 22), ("0.0.0.0", 0))

#         self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#         try:
#             self.ssh.connect(
#                 self.instance.metadata.network.nic_allocation.addresses[0], # nodes should be setup in /etc/hosts correctly
#                 username="root",
#                 pkey=paramiko.RSAKey.from_private_key(io.StringIO(self.instance.metadata.root_user.mgmt_ssh_private_key)),
#                 port=22,
#                 sock=self.jump_channel
#             )
#             self.sftp = self.ssh.open_sftp()
#             # Cache usernames and groups

#             with self.sftp.open("/etc/passwd") as file:
#                 for line in file:
#                     s = line.split(":")
#                     self._uids[s[0]] = int(s[2])
#                     self._usernames[int(s[2])] = s[0]

#             with self.sftp.open("/etc/group") as file:
#                 for line in file:
#                     s = line.split(":")
#                     self._gids[s[0]] = int(s[2])
#                     self._groupnames[int(s[2])] = s[0]

#         except ConnectionError as e:
#             raise exceptions.resource.Unavailable("Could not connect to instance. Is SSH by root ssh key turned off")

#         return self


#     def get_uid(self, username: str) -> int:
#         if username in self._uids:
#             return self._uids[username]

#         raise exceptions.resource.Unavailable()

#     def get_username(self, uid: int) -> str:
#         if uid in self._usernames:
#             return self._usernames[uid]

#         raise exceptions.resource.Unavailable()

#     def get_group(self, gid: int) -> str:
#         if gid in self._groupnames:
#             return self._groupnames[gid]

#         raise exceptions.resource.Unavailable()

#     def get_gid(self, group: str) -> int:
#         if group in self._gids:
#             return self._gids[group]

#         raise exceptions.resource.Unavailable()

#     def __exit__(self, type, value, traceback):
#         self.sftp.close()
#         self.ssh.close()
#         self.jump.close()

def build_proxmox_config_string(options: dict):
    """Turns a dict into string of e.g.'key1=value1,key2=value2'"""
    return ",".join(map(lambda d: f"{d[0]}={d[1]}", options.items()))

class Proxmox():
    def __init__(self):
        if config.proxmox.cluster.api.password:
            self.prox = ProxmoxAPI(
                host=config.proxmox.cluster.api.server,
                user=config.proxmox.cluster.api.username,
                password=config.proxmox.cluster.api.password,
                port=config.proxmox.cluster.api.port,
                verify_ssl=False
            )
        else:
            self.prox = ProxmoxAPI(
                host=config.proxmox.cluster.api.server,
                user=config.proxmox.cluster.api.username,
                token_name=config.proxmox.cluster.api.token_name,
                token_value=config.proxmox.cluster.api.token_value,
                port=config.proxmox.cluster.api.port,
                verify_ssl=False
            )

    def get_templates(
        self,
        instance_type: models.proxmox.Type
    ) -> Dict[str, models.proxmox.Template]:
        if instance_type == models.proxmox.Type.LXC:
            return config.proxmox.lxc.templates
        elif instance_type == models.proxmox.Type.VPS:
            return config.proxmox.vps.templates

    def get_template(
        self,
        instance_type: models.proxmox.Type,
        template_id: str
    ) -> models.proxmox.Template:
        templates = self.get_templates(instance_type)
        if template_id not in templates:
            raise exceptions.rest.Error(
                400,
                models.rest.Detail(
                    msg=f"Template {template_id} does not exist!"
                )
            )
        else:
            return templates[template_id]

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

            if node_name in config.proxmox.blacklisted_nodes:
                del scoreboard[node_name]

        # return the node with the highest score
        return sorted(scoreboard, key=scoreboard.get, reverse=True)[0]

    def _get_instance_fqdn_for_username(
        self,
        instance_type: models.proxmox.Type,
        username: str,
        hostname: str
    ) -> str:
        if instance_type == models.proxmox.Type.LXC:
            return f"{hostname}.{username}.{config.proxmox.lxc.base_fqdn}"
        elif instance_type == models.proxmox.Type.VPS:
            return f"{hostname}.{username}.{config.proxmox.vps.base_fqdn}"

    def _get_instance_fqdn_for_account(
        self,
        instance_type: models.proxmox.Type,
        account: models.account.Account,
        hostname: str
    ) -> str:
        return self._get_instance_fqdn_for_username(instance_type, account.username, hostname)

    def _allocate_nic(
        self,
        instance_type: models.proxmox.Type
    ) -> models.proxmox.NICAllocation:
        # world's most ghetto ip allocation algorithm
        network = config.proxmox.network.network.network
        base_ip = config.proxmox.network.network.ip
        gateway = base_ip + 1

        # returns set with network and broadcast address removed
        ips = set(network.hosts())

        # list of possible ips an instance can have
        allowed_ips = functools.reduce(
            lambda x,y: x+y,
            map(
                list,
                [ipaddr for ipaddr in ipaddress.summarize_address_range(
                    config.proxmox.network.range[0],
                    config.proxmox.network.range[1]
                )]
            ), []
        )

        ips = ips.intersection(allowed_ips)

        if gateway in ips:
            ips.remove(gateway)

        # remove any addresses assigned to any of the other instances
        for fqdn, instance in self.read_instances().items():
            for address in instance.metadata.network.nic_allocation.addresses:
                if address.ip in ips:
                    ips.remove(address.ip)
    
        if len(ips) > 0:
            ip_addr = next(iter(ips))

            return models.proxmox.NICAllocation(
                addresses=[
                    ipaddress.IPv4Interface(f"{ip_addr}/{network.prefixlen}")
                ],
                gateway4=gateway,
                macaddress="02:00:00:%02x:%02x:%02x" % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
                vlan=config.proxmox.network.vlan
            )
        else:
            raise exception.resource.Unavailable("Could not allocate an IP for the instance. No IPs available")

    def _serialize_metadata(
        self,
        metadata: models.proxmox.Metadata
    ):
        # https://github.com/samuelcolvin/pydantic/issues/1043
        return yaml.safe_dump(
            yaml.safe_load(metadata.json()),
            default_flow_style=False,
            explicit_start=None,
            default_style='', width=8192
        )

    def write_out_instance_metadata(
        self,
        instance: models.proxmox.Instance
    ):
        yaml_description = self._serialize_metadata(instance.metadata)
        
        if instance.type == models.proxmox.Type.LXC:
            self.prox.nodes(f"{instance.node}/lxc/{instance.id}/config").put(description=yaml_description)
        elif instance.type == models.proxmox.Type.VPS:
            self.prox.nodes(f"{instance.node}/qemu/{instance.id}/config").put(description=yaml_description)

    def _hash_fqdn(
        self,
        fqdn: str
    ) -> int:
        random.seed(fqdn)
        hash_id = random.randint(1000, 5000000)
        random.seed()

        return hash_id

    def _ensure_template_present(
        self,
        node_name: str,
        template: models.proxmox.Template,
        folder_path: str
    ) -> str:
        """Downloads the speciied template to the specified path (must be a folder) and returns the full path of the image file onto the node name specified"""

        # Download the disk image/template
        
        image_path = f"{folder_path}/{template.disk_file}"
        # needs to be unique as this could be happening on multiple workers and we don't want them to overwrite the ile mid download
        download_path = f"{folder_path}/{socket.gethostname()}-{os.getpid()}"

        with ClusterNodeSSH(node_name) as con:
            stdin, stdout, stderr = con.ssh.exec_command(
                f"mkdir -p {folder_path}"
            )
            status = stdout.channel.recv_exit_status()

            if status != 0:
                raise exceptions.resource.Unavailable(f"Could not download template: could not reserve download dir {stderr.read()}")

            # See if the image exists
            try:
                logger.info(image_path)
                con.sftp.stat(image_path)

                if template.disk_sha256sum is not None:
                    # Checksum image    
                    stdin, stdout, stderr = con.ssh.exec_command(
                        f"sha256sum {image_path} | cut -f 1 -d' '"
                    )

                    if template.disk_sha256sum not in str(stdout.read()):
                        logger.info(f"Template does not pass SHA256 sums given, falling back to download", status=status, stderr=stderr.read(), stdout=stdout.read())
                        raise exceptions.resource.Unavailable()

            except (exceptions.resource.Unavailable, FileNotFoundError) as e:
                # If a fallback URL exists to download the image
                logger.info("Could not find file, falling back to download", template=template.dict(), e=e, exc_info=True)

                if template.disk_file_fallback_url is not None:
                    # Original image does not exist, we gotta download it
                    stdin, stdout, stderr = con.ssh.exec_command(
                        f"wget {template.disk_file_fallback_url} -O {download_path}"
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
                        raise exceptions.resource.Unavailable(f"Couldn't rename template {status}: {stderr.read()} {stdout.read()}")
                else:
                    raise exceptions.resource.Unavailable(f"This template is currently unavailable: no fallback URL for template")
   
        return image_path

    def create_instance(
        self,
        instance_type: models.proxmox.Type,
        account: models.account.Account,
        hostname: str,
        request_detail: models.proxmox.InstanceRequestDetail
    ) -> Tuple[str,str]:

        template = self.get_template(instance_type, request_detail.template_id)

        try:
            existing_vm = self.read_instance_by_account(instance_type, account, hostname)
            raise exceptions.resource.AlreadyExists(f"Instance {hostname} already exists")
        except exceptions.resource.NotFound:
            pass

        node_name = self._select_best_node(template.specs)
        fqdn = self._get_instance_fqdn_for_account(instance_type, account, hostname)

        pool_folder_path = None

        if instance_type == models.proxmox.Type.LXC:
            if template.disk_format != models.proxmox.Template.DiskFormat.TarGZ:
                raise exceptions.resource.Unavailable(f"Templates (on Container instances) {detail.template_id} must use TarGZ of RootFS format!")

            pool_folder_path = f"{self.prox.storage(config.proxmox.dir_pool).get()['path']}/template/cache"
        elif instance_type == models.proxmox.Type.VPS:
            if template.disk_format != models.proxmox.Template.DiskFormat.QCOW2:
                raise exceptions.resource.Unavailable(f"Templates (on VPS instances) {detail.template_id} must use QCOW2 disk image format!")

            pool_folder_path = f"{self.prox.storage(config.proxmox.dir_pool).get()['path']}/template/vps" 

        # Checks that template exists & tries to download it if it doesn't
        disk_image_path = self._ensure_template_present(
            node_name,
            template,
            pool_folder_path
        )

        # Give the host it's fqdn by default as a vhost
        # (we allow this in validate_domain)
        vhosts_dict = {}
        vhosts_dict[fqdn] = models.proxmox.VHostOptions(
            https=False,
            port=80
        )

        password, user_ssh_private_key, root_user = self._generate_instance_root_user()

        metadata = models.proxmox.Metadata(
            owner=account.username,
            request_detail=request_detail,
            inactivity=models.proxmox.Inactivity(
                marked_active_at=datetime.date.today()
            ),
            network=models.proxmox.Network(
                nic_allocation=self._allocate_nic(instance_type),
                vhosts=vhosts_dict
            ),
            root_user=root_user,
            wake_on_request=template.wake_on_request
        )

        hash_id = self._hash_fqdn(fqdn)

        # Store VM metadata in the description field
        yaml_description = self._serialize_metadata(metadata)

        if instance_type == models.proxmox.Type.LXC:
            metadata.groups = set(["lxc", "cloud_lxc", "cloud_instance"])

            self.prox.nodes(f"{node_name}/lxc").post(**{
                "hostname": fqdn,
                "vmid": hash_id,
                "description": yaml_description,
                "ostemplate": f"{config.proxmox.dir_pool}:vztmpl/{template.disk_file}",
                "cores": template.specs.cores,
                "memory": template.specs.memory,
                "swap": template.specs.swap,
                "storage": config.proxmox.dir_pool,
                "unprivileged": 1,
                "nameserver": "1.1.1.1"
            })
    
            self._wait_for_instance_created(instance_type, fqdn)

            instance = self._read_instance_by_fqdn(instance_type, fqdn)

            # Enable nesting so they can use Docker
            with ClusterNodeSSH(instance.node) as con:
                # Copy disk image
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"pvesh set /nodes/{ instance.node }/lxc/{ instance.id }/config -features keyctl=1,nesting=1"
                )

                status = stdout.channel.recv_exit_status()
                
                if status != 0:
                    raise exceptions.resource.Unavailable(f"Couldn't enable instance nesting {status}: {stderr.read()} {stdout.read()}")

            self.prox.nodes(instance.node).lxc(f"{instance.id}/resize").put(
                disk='rootfs',
                size=f'{template.specs.disk_space}G'
            )

            self._wait_vmid_lock(instance.type, instance.node, instance.id)

        elif instance_type == models.proxmox.Type.VPS:
            metadata.groups = set(["vm", "cloud_vm", "cloud_instance"])

            stub_vm_name = f"stub-{fqdn}-{socket.gethostname()}-{os.getpid()}-{time.time()}"

            # we need to create a 'stub' vm to reserve an id
            # the vm disk image is stored in a folder named as the id so we need to create the vm before we configure it to discover this id
            logger.info("created")
            self.prox.nodes(f"{node_name}/qemu").post(
                name=stub_vm_name,
                vmid=hash_id
            )

            # now find the vm by its name, we can't trust the hash_id because if there's a collision it'l be + 1
            vm_id = None

            for vm in self.prox.nodes(node_name).qemu.get():
                if vm['name'] == stub_vm_name:
                    vm_id = vm['vmid']
                    break

            if vm_id is None:
                raise exceptions.resource.Unavailable(f"Unable to find created stub vm")

            # if theres an error anywhere in the process, we will call this function to nuke the stub vm
            def cleanup_stub():
                self.prox.nodes(instance.node).qemu(vm_id).delete()

            vms_images_path = self.prox.storage(config.proxmox.dir_pool).get()['path'] + "/images"

            with ClusterNodeSSH(node_name) as con:
                # Copy disk image
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"cd {vms_images_path} && rm -f {vm_id} && mkdir {vm_id} && cd {vm_id} && cp {disk_image_path} ./primary.{ template.disk_format }"
                )
                status = stdout.channel.recv_exit_status()
                
                if status != 0:
                    cleanup_stub()
                    raise exceptions.resource.Unavailable(f"Couldn't create instance disk image {status}: {stderr.read()} {stdout.read()}")

                # Create disk for EFI
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"cd {vms_images_path}/{vm_id} && qemu-img create -f qcow2 efi.qcow2 128K"
                )
                status = stdout.channel.recv_exit_status()
                
                if status != 0:
                    cleanup_stub()
                    raise exceptions.resource.Unavailable(f"Couldn't create instance EFI image {status}: {stderr.read()} {stdout.read()}")

            # Reconfigure stub
            self.prox.nodes(f"{node_name}/qemu/{vm_id}/config").put(
                name=fqdn,
                agent=1,
                description=yaml_description,
                virtio0=f"{config.proxmox.dir_pool}:{vm_id}/primary.{ template.disk_format }",
                cores=template.specs.cores,
                memory=template.specs.memory,
                balloon=min(template.specs.memory, 256),
                bios='ovmf',
                efidisk0=f"{config.proxmox.dir_pool}:{vm_id}/efi.qcow2",
                scsihw='virtio-scsi-pci',
                machine='q35',
                serial0='socket',
                bootdisk='virtio0'
            )

            self._wait_vmid_lock(instance_type, node_name, vm_id)

            self.prox.nodes(node_name).qemu(f"{vm_id}/resize").put(
                disk='virtio0',
                size=f'{template.specs.disk_space}G'
            )

            self._wait_vmid_lock(instance_type, node_name, vm_id)

    def delete_instance(
        self,
        instance: models.proxmox.Instance
    ):
        if instance.status != models.proxmox.Status.Stopped:
            raise exceptions.resource.Unavailable("Cannot delete instance, instance is running")

        if instance.type == models.proxmox.Type.LXC:
            self.prox.nodes(instance.node).lxc(f"{instance.id}").delete()
        elif instance.type == models.proxmox.Type.VPS:
            # delete cloud-init data
            with ClusterNodeSSH(instance.node) as con:
                snippets_path = self.prox.storage(config.proxmox.dir_pool).get()['path'] + "/snippets"

                stdin, stdout, stderr = con.ssh.exec_command(
                    f"rm -f '{ snippets_path }/{instance.fqdn}.networkconfig.yml' '{ snippets_path }/{instance.fqdn}.userdata.yml' '{ snippets_path }/{instance.fqdn}.metadata.yml'"
                )

            self.prox.nodes(instance.node).qemu(f"{instance.id}").delete()

    def _wait_vmid_lock(
        self,
        instance_type: models.proxmox.Type,
        node_name: str,
        vm_id: int,
        timeout: int = 25,
        poll_interval: int = 1
    ):
        """Waits for Proxmox to unlock the VM, it typically locks it when it's resizing a disk/creating a vm/etc..."""
        start = time.time()
        while True:
            if instance_type == models.proxmox.Type.LXC:
                res = self.prox.nodes(node_name).lxc(f"{vm_id}/config").get()
            elif instance_type == models.proxmox.Type.VPS:
                res = self.prox.nodes(node_name).qemu(f"{vm_id}/config").get()


            if 'lock' not in res: 
                break

            now = time.time()
            if (now-start) > timeout:
                raise exceptions.resource.Unavailable("Timeout occured waiting for instance to unlock.")

            time.sleep(poll_interval)

    def _wait_for_instance_created(
        self,
        instance_type: models.proxmox.Type,
        fqdn: str,
        timeout: int = 60,
        poll_interval: int = 1
    ):
        """Wait for an instance of the specified name to appear in the Proxmox cluster"""

        created = False
        start = time.time()
        while not created:
            now = time.time()

            lxcs_qemus = self.prox.cluster.resources.get(type="vm")

            for entry in lxcs_qemus:
                if 'name' in entry and entry['name'] == fqdn:
                    if instance_type == models.proxmox.Type.LXC:
                        config = self.prox.nodes(f"{entry['node']}/lxc/{entry['vmid']}/config").get()

                        # logger.info(config)
                        if 'lock' not in config and 'hostname' in config and config['hostname'] == fqdn:
                            return

                    elif instance_type == models.proxmox.Type.VPS:
                        config = self.prox.nodes(f"{entry['node']}/qemu/{entry['vmid']}/config").get()

                        if 'name' in config and config['name'] == fqdn and 'lock' not in config:
                            return

            if (now-start) > timeout:
                raise exceptions.resource.Unavailable(f"Timeout occured waiting for instance to created")

            time.sleep(poll_interval)


    def _wait_for_instance_status(
        self,
        instance: models.proxmox.Instance,
        wait_for_status: models.proxmox.Status = models.proxmox.Status.Running,
        timeout: int = 25,
        poll_interval: int = 1
    ):
        """Waits for Proxmox to unlock the VM, it typically locks it when it's resizing a disk/creating a vm/etc..."""
        start = time.time()
        while True:
            now = time.time()

            if instance.type == models.proxmox.Type.LXC:
                current = self.prox.nodes(instance.node).lxc(f"{instance.id}/status/current").get()
            elif instance.type == models.proxmox.Type.VPS:
                current = self.prox.nodes(instance.node).qemu(f"{instance.id}/status/current").get()

            logger.info("wait_for_instance_status", current=current['status'], wait_for_status=wait_for_status)

            if current['status'] == 'running' and wait_for_status == models.proxmox.Status.Running:
                break
            
            if current['status'] == 'stopped' and wait_for_status == models.proxmox.Status.Stopped:
                break


            if (now-start) > timeout:
                raise exceptions.resource.Unavailable(f"Timeout occured waiting for instance to change from {current['status']} status")

            time.sleep(poll_interval)

    def _read_instance_on_node(
        self,
        instance_type: models.proxmox.Type,
        node: str,
        vmid: int,
        expected_fqdn: Optional[str] = None
    ) -> models.proxmox.Instance:

        if instance_type == models.proxmox.Type.LXC:
            try:
                lxc_config = self.prox.nodes(f"{node}/lxc/{vmid}/config").get()
            except Exception as e:
                raise exceptions.resource.NotFound("The instance does not exist")

            fqdn = lxc_config['hostname']

            if expected_fqdn is not None and fqdn != expected_fqdn:
                raise exceptions.resource.NotFound("The instance at the specified VM ID does not have the expected FQDN")

            # decode description
            try:
                metadata = models.proxmox.Metadata.parse_obj(
                    yaml.safe_load(lxc_config['description'])
                )
            except Exception as e:
                raise exceptions.resource.Unavailable(
                    f"Instance is unavailable, malformed metadata description: {e}"
                )

            # for user ocanty, returns .ocanty.lxc.cloud.netsoc.co
            suffix = self._get_instance_fqdn_for_username(instance_type, metadata.owner, "")

            # trim suffix
            if not fqdn.endswith(suffix):
                raise exceptions.resource.Unavailable(
                    f"Found but Owner / FQDN do not align, FQDN is {lxc_fqdn} but owner is {metadata.owner}"
                )

            hostname = fqdn[:-len(suffix)]

            # An instance is considered active if the time it was last marked active is within the allowed active before shutdown period
            if config.proxmox.lxc.inactivity_shutdown_num_days > (datetime.date.today() - metadata.inactivity.marked_active_at).days:
                active = True
            else:
                active = False

            # If the instance is marked permanent, this overrides the activity period
            if metadata.permanent == True:
                active = True

            # If the instance is suspended for ToS violations, we mark the instance as always inactive
            if metadata.tos.suspended == True:
                active = False

            shutdown_date = metadata.inactivity.marked_active_at + datetime.timedelta(config.proxmox.lxc.inactivity_shutdown_num_days)
            deletion_date = metadata.inactivity.marked_active_at + datetime.timedelta(config.proxmox.lxc.inactivity_deletion_num_days)

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

            current_status = self.prox.nodes(f"{node}/lxc/{vmid}/status/current").get()
            if current_status['status'] == 'running':
                status = models.proxmox.Status.Running
            elif current_status['status'] == 'stopped':
                status = models.proxmox.Status.Stopped

            instance = models.proxmox.Instance(
                type=instance_type,
                id=vmid,
                fqdn=fqdn,
                hostname=hostname,
                node=node,
                metadata=metadata,
                inactivity_shutdown_date=shutdown_date,
                inactivity_deletion_date=deletion_date,
                specs=specs,
                remarks=[],
                status=status,
                active=active
            )

            # Build remarks about the thing, problems, etc...
            for vhost in instance.metadata.network.vhosts:
                valid, remarks = self.validate_domain(instance, vhost)

                if valid is not True:
                    instance.remarks += remarks

            return instance
        elif instance_type == models.proxmox.Type.VPS:
            try:
                vm_config = self.prox.nodes(f"{node}/qemu/{vmid}/config").get()
            except Exception as e:
                raise exceptions.resource.NotFound("The instance does not exist")

            fqdn = vm_config['name']

            if expected_fqdn is not None and fqdn != expected_fqdn:
                raise exceptions.resource.NotFound("The instance at the specified VM ID does not have the expected FQDN")
            
            # decode description
            try:
                metadata = models.proxmox.Metadata.parse_obj(
                    yaml.safe_load(vm_config['description'])
                )
            except Exception as e:
                raise exceptions.resource.Unavailable(
                    f"Instance is unavailable, malformed metadata description: {e}"
                )

            suffix = self._get_instance_fqdn_for_username(instance_type, metadata.owner, "")

            # trim suffix
            if not fqdn.endswith(suffix):
                raise exceptions.resource.Unavailable(
                    f"Found Instance but Owner / FQDN do not align, FQDN is {fqdn} but owner is {metadata.owner}"
                )

            hostname = fqdn[:-len(suffix)]

            # An instance is considered active if the time it was last marked active is within the allowed active before shutdown period
            if config.proxmox.vps.inactivity_shutdown_num_days > (datetime.date.today() - metadata.inactivity.marked_active_at).days:
                active = True
            else:
                active = False

            # If the instance is marked permanent, this overrides the activity period
            if metadata.permanent == True:
                active = True

            # If the instance is suspended for ToS violations, we mark the instance as always inactive
            if metadata.tos.suspended == True:
                active = False

            # config str looks like this: whatever,size=30G
            # extract the size str
            size_str = dict(map(lambda x: (x.split('=') + [""])[:2], vm_config['virtio0'].split(',')))['size']

            disk_space = int(size_str[:-1])

            specs = models.proxmox.Specs(
                cores=vm_config['cores'],
                memory=vm_config['memory'],
                swap=vm_config['swap'] if 'swap' in vm_config else 0,
                disk_space=disk_space
            )

            current_status = self.prox.nodes(f"{node}/qemu/{vmid}/status/current").get()
            if current_status['status'] == 'running':
                status = models.proxmox.Status.Running
            elif current_status['status'] == 'stopped':
                status = models.proxmox.Status.Stopped

            shutdown_date = metadata.inactivity.marked_active_at + datetime.timedelta(config.proxmox.vps.inactivity_shutdown_num_days)
            deletion_date = metadata.inactivity.marked_active_at + datetime.timedelta(config.proxmox.vps.inactivity_deletion_num_days)

            instance = models.proxmox.Instance(
                type=instance_type,
                id=vmid,
                fqdn=fqdn,
                hostname=hostname,
                node=node,
                metadata=metadata,
                inactivity_shutdown_date=shutdown_date,
                inactivity_deletion_date=deletion_date,
                specs=specs,
                remarks=[],
                status=status,
                active=active
            )

            # Build remarks about the thing, problems, etc...
            for vhost in instance.metadata.network.vhosts:
                valid, remarks = self.validate_domain(instance, vhost)

                if valid is not True:
                    instance.remarks += remarks

            return instance

        raise exceptions.resource.NotFound("The instance does not exist")

    def _read_instance_by_fqdn(
        self,
        instance_type: models.proxmox.Type,
        fqdn: str
    ) -> models.proxmox.Instance:
        lxcs_qemus = self.prox.cluster.resources.get(type="vm")

        for entry in lxcs_qemus:
            if 'name' in entry and entry['name'] == fqdn:
                instance = self._read_instance_on_node(instance_type, entry['node'], entry['vmid'])
                return instance

        raise exceptions.resource.NotFound("The instance does not exist")

    def read_instance_by_account(
        self,
        instance_type: models.proxmox.Type,
        account: models.account.Account,
        hostname: str
    ) -> models.proxmox.Instance:
        return self._read_instance_by_fqdn(
            instance_type,
            self._get_instance_fqdn_for_account(instance_type, account, hostname)
        )

    def read_instances_by_account(
        self,
        instance_type: models.proxmox.Type,
        account: models.account.Account,
        ignore_errors: bool = True
    ) -> Dict[str, models.proxmox.Instance]:
        
        ret = { }

        lxcs_qemus = self.prox.cluster.resources.get(type="vm")
        
        for entry in lxcs_qemus:
            if 'name' in entry and entry['name'].endswith(self._get_instance_fqdn_for_account(instance_type, account, "")):
                if ignore_errors == True:
                    try:
                        instance = self._read_instance_on_node(instance_type, entry['node'], entry['vmid'])
                        ret[instance.hostname] = instance
                    except Exception as e:
                        logger.info("read_instances_by_account ignoring instance with error", ignore_errors=ignore_errors, account=account)
                else:
                    instance = self._read_instance_on_node(instance_type, entry['node'], entry['vmid'])
                    ret[instance.hostname] = instance
                        
        return ret

    def read_instances(
        self,
        instance_type: Optional[models.proxmox.Type] = None,
        ignore_errors: bool = True
    ) -> Dict[str, models.proxmox.Instance]:

        ret = { }

        lxcs_qemus = self.prox.cluster.resources.get(type="vm")

        for entry in lxcs_qemus:
            if entry['type'] == 'qemu' and (instance_type == None or instance_type == models.proxmox.Type.VPS) and 'name' in entry and entry['name'].endswith(config.proxmox.vps.base_fqdn):
                if ignore_errors == True:
                    try:
                        instance =  self._read_instance_on_node(models.proxmox.Type.VPS, entry['node'], entry['vmid'])
                        ret[instance.fqdn] = instance
                    except Exception as e:
                        logger.info("read_instances ignoring instance with error", ignore_errors=ignore_errors, entry=entry, exc_info=True, e=e)
                else:
                    instance = self._read_instance_on_node(models.proxmox.Type.VPS, entry['node'], entry['vmid'])
                    ret[instance.fqdn] = instance
            elif entry['type'] == 'lxc' and (instance_type == None or instance_type == models.proxmox.Type.LXC) and 'name' in entry and entry['name'].endswith(config.proxmox.lxc.base_fqdn):
                if ignore_errors == True:
                    try:
                        instance = self._read_instance_on_node(models.proxmox.Type.LXC, entry['node'], entry['vmid'])
                        ret[instance.fqdn] = instance
                    except Exception as e:
                        logger.info("read_instances ignoring instance with error", ignore_errors=ignore_errors, entry=entry, exc_info=True, e=e)
                else:
                    instance = self._read_instance_on_node(models.proxmox.Type.LXC, entry['node'], entry['vmid'])
                    ret[instance.fqdn] = instance
            
        return ret


    def _generate_instance_root_user(
        self
    ) -> Tuple[str, str, models.proxmox.RootUser]:
        ssh_public_key, ssh_private_key = utilities.ssh.generate_key_pair()

        password = utilities.password.generate()

        return password, ssh_private_key, models.proxmox.RootUser(
            password_hash=utilities.password.hash(password),
            ssh_public_key=ssh_public_key,
        )

    def _wait_for_qemu_guest_agent_ping(
        self,
        instance: models.proxmox.Instance,
        timeout: int = 25,
        poll_interval: int = 1
    ):
        """Waits for the qemu-guest-agent process to start on a vm"""

        if instance.type != models.proxmox.Type.VPS:
            raise exceptions.resource.Unavailable("Can't wait on guest agent for non QEMU VM")

        start = time.time()
        while True:
            now = time.time()

            try:
                self.prox.nodes(instance.node).qemu(f"{instance.id}/agent/ping").post()
                # throws an error if ping fails, we ignore error in exception handler
                # if ping is successful break out of the loop
                break
            except Exception as e:
                pass

            if (now-start) > timeout:
                raise exceptions.resource.Unavailable(f"Timeout occured waiting for instance to start qemu-guest-agent")

            time.sleep(poll_interval)

    def reset_instance_root_user(
        self,
        instance: models.proxmox.Instance,
        root_user: Optional[models.proxmox.RootUser] = None
    ) -> Tuple[str, str, models.proxmox.RootUser]:
        """Returns a tuple of password, private_key"""

        if instance.status == models.proxmox.Status.Stopped:
            raise exceptions.resource.Unavailable("Instance must be running to reset root user")

        if root_user is None:
            password, user_ssh_private_key, root_user = self._generate_instance_root_user()

        self._wait_vmid_lock(instance.type, instance.node, instance.id)

        if instance.type == models.proxmox.Type.LXC:
            with ClusterNodeSSH(instance.node) as con:
                # Install root password
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"echo -e 'root:{root_user.password_hash}' | pct exec {instance.id} -- chpasswd -e"
                )
                status = stdout.channel.recv_exit_status()

                if status != 0:
                    raise exceptions.resource.Unavailable(
                        f"Could not start instance: unable to set root password: {status}: {stdout.read()} {stderr.read()}"
                    )

                stdin, stdout, stderr = con.ssh.exec_command(
                    f"pct exec {instance.id} -- mkdir -p /root/.ssh"
                )
                status = stdout.channel.recv_exit_status()

                if status != 0:
                    raise exceptions.resource.Unavailable(
                        f"Could not start instance: unable to create /root/.ssh: {status}: {stdout.read()} {stderr.read()}"
                    )

                # Install ssh keys
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"echo -e '# --- BEGIN PVE ---\\n{root_user.ssh_public_key}\\n# --- END PVE ---' | pct push { instance.id } /dev/stdin '/root/.ssh/authorized_keys' --perms 0600 --user 0 --group 0"
                )
                status = stdout.channel.recv_exit_status()

                if status != 0:
                    raise exceptions.resource.Unavailable(
                        f"Could not start instance: unable to inject ssh keys {status}: {stdout.read()} {stderr.read()}"
                    )
                
                # Install banner
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"echo -e \"{ templates.sshd.banner.render() }\" | pct push { instance.id } /dev/stdin '/etc/banner' --perms 0644 --user 0 --group 0"
                )
                status = stdout.channel.recv_exit_status()

                if status != 0:
                    raise exceptions.resource.Unavailable(
                        f"Could not start instance: could not install banner {status}: {stdout.read()} {stderr.read()}"
                    )

                # Install sshd config
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"echo -e \"{ templates.sshd.config_allow_root_login.render(banner_path='/etc/banner') }\" | pct push { instance.id } /dev/stdin '/etc/ssh/sshd_config' --perms 0644 --user 0 --group 0"
                )
                status = stdout.channel.recv_exit_status()

                if status != 0:
                    raise exceptions.resource.Unavailable(
                        f"Could not start instance: unable to reset ssh configuration {status}: {stdout.read()} {stderr.read()}"
                    )

                stdin, stdout, stderr = con.ssh.exec_command(
                    f"pct exec {instance.id} -- service ssh restart"
                )
                status = stdout.channel.recv_exit_status()

                if status != 0:
                    raise exceptions.resource.Unavailable(
                        f"Could not start instance: unable to (re)start sshd server: {status}: {stdout.read()} {stderr.read()}"
                    )

        elif instance.type == models.proxmox.Type.VPS:
            self._wait_for_qemu_guest_agent_ping(instance)

            self.prox.nodes(instance.node).qemu(f"{instance.id}/agent/exec").post(**{
                'command': f'passwd -u root'
            })

            self.prox.nodes(instance.node).qemu(f"{instance.id}/agent/set-user-password").post(**{
                'username': 'root',
                'password': root_user.password_hash,
                'crypted': '1'
            })

            self.prox.nodes(instance.node).qemu(f"{instance.id}/agent/exec").post(**{
                'command': 'mkdir -p /root/.ssh',
            })

            self.prox.nodes(instance.node).qemu(f"{instance.id}/agent/file-write").post(
                file="/root/.ssh/authorized_keys",
                content=f"# --- BEGIN PVE ---\n{root_user.ssh_public_key}\n# --- END PVE ---"
            )

            self.prox.nodes(instance.node).qemu(f"{instance.id}/agent/file-write").post(
                file="/etc/ssh/sshd_config",
                content=templates.sshd.config_allow_root_login.render(banner_path='/etc/banner')
            )

            self.prox.nodes(instance.node).qemu(f"{instance.id}/agent/file-write").post(
                file="/etc/banner",
                content=re.sub(r'[^\x00-\xff]',r'', templates.sshd.banner.render())
            )

            self.prox.nodes(instance.node).qemu(f"{instance.id}/agent/exec").post(
                command="service ssh restart",
            )

        instance.metadata.root_user = root_user
        self.write_out_instance_metadata(instance)

        return password, user_ssh_private_key, root_user

    def start_instance(
        self,
        instance: models.proxmox.Instance,
        vps_clear_cloudinit: bool = False
    ):
        if instance.type == models.proxmox.Type.LXC:
            self.prox.nodes(instance.node).lxc(f"{instance.id}/config").put(**{
                "nameserver": "1.1.1.1",
                "net0": build_proxmox_config_string({
                    "rate": "12.5", # 12.5MB/s
                    "name": "eth0",
                    "bridge": config.proxmox.network.bridge,
                    "tag": instance.metadata.network.nic_allocation.vlan,
                    "hwaddr": instance.metadata.network.nic_allocation.macaddress,
                    "ip": instance.metadata.network.nic_allocation.addresses[0],
                    "gw": instance.metadata.network.nic_allocation.gateway4,
                    "mtu": 1450 # if we ever decide to move to vxlan
                })
            })

            self.prox.nodes(instance.node).lxc(f"{instance.id}/firewall/options").put(**{
                "macfilter": 1,
                "ipfilter": 1
            })


            self.prox.nodes(instance.node).lxc(f"{instance.id}/status/start").post()
        elif instance.type == models.proxmox.Type.VPS:
            # delete cloud-init data
            with ClusterNodeSSH(instance.node) as con:
                snippets_path = self.prox.storage(config.proxmox.dir_pool).get()['path'] + "/snippets"

                stdin, stdout, stderr = con.ssh.exec_command(
                    f"rm -f '{ snippets_path }/{instance.fqdn}.networkconfig.yml' '{ snippets_path }/{instance.fqdn}.userdata.yml' '{ snippets_path }/{instance.fqdn}.metadata.yml'"
                )

                # Detach existing cloud-init drive (if any)
                self.prox.nodes(instance.node).qemu(f"{instance.id}/config").put(
                    ide2="none,media=cdrom",
                    cicustom=""
                )

                # install cloud-init data
                snippets_path = self.prox.storage(config.proxmox.dir_pool).get()['path'] + "/snippets"


                if vps_clear_cloudinit == True:
                    # This will wipe previous cloud-init state from previous boot then shutdown
                    # On the next boot, cloudinit will reapply without this bool set to true
                    userdata_config = f"""#cloud-config
bootcmd:
    - rm -f /etc/netplan/50-cloud-init.yaml
    - cloud-init clean --logs
    - rm -Rf /var/lib/cloud/*
    - shutdown now
"""         
                else:
                    # cloud-init has a complete allergy to modifying the root user so we need to do a lot of this
                    # the non-traditional way
                    userdata_config = f"""#cloud-config
preserve_hostname: false
manage_etc_hosts: true
fqdn: { instance.fqdn }
packages:
    - qemu-guest-agent
chpasswd:
    expire: false
disable_root: false
ssh_pwauth: true
runcmd:
    - [ systemctl, enable, qemu-guest-agent ]
    - [ systemctl, start, qemu-guest-agent, --no-block ]  
"""

                network_config = f"""---
ethernets:
    net0:
        match:
            macaddress: { instance.metadata.network.nic_allocation.macaddress }
        nameservers:
            addresses:
                - 1.1.1.1
                - 8.8.8.8
        gateway4: { config.proxmox.network.gateway }
        optional: true
        link-local: []
        addresses:
            - { instance.metadata.network.nic_allocation.addresses[0] }
        mtu: 1450 
version: 2
"""

                con.sftp.putfo(
                    io.StringIO(network_config),
                    f'{ snippets_path }/{instance.fqdn}.networkconfig.yml'
                )

                con.sftp.putfo(
                    io.StringIO(userdata_config),
                    f'{ snippets_path }/{instance.fqdn}.userdata.yml'
                )

                con.sftp.putfo(
                    io.StringIO(""),
                    f'{ snippets_path }/{instance.fqdn}.metadata.yml'
                )

            # Insert cloud-init drive
            self.prox.nodes(instance.node).qemu(f"{instance.id}/config").put(
                cicustom=build_proxmox_config_string({
                    "user": f"{ config.proxmox.dir_pool }:snippets/{instance.fqdn}.userdata.yml",
                    "network": f"{ config.proxmox.dir_pool }:snippets/{instance.fqdn}.networkconfig.yml",
                    "meta": f"{ config.proxmox.dir_pool }:snippets/{instance.fqdn}.metadata.yml"
                }),
                ide2=f"{ config.proxmox.dir_pool }:cloudinit,format=qcow2"
            )

            # Set network card
            self.prox.nodes(instance.node).qemu(f"{instance.id}/config").put(
                net0=build_proxmox_config_string({
                    "virtio": instance.metadata.network.nic_allocation.macaddress,
                    "bridge": config.proxmox.network.bridge,
                    "tag": instance.metadata.network.nic_allocation.vlan,
                    "rate": "12.5" # 12.5MBps
                })
            )

            
            # Setup IP/ARP filter to prevent spoofing attacks
            self.prox.nodes(instance.node).qemu(f"{instance.id}/firewall/options").put(**{
                "macfilter": 1,
                "ipfilter": 1
            })

            for i in range(len(instance.metadata.network.nic_allocation.addresses)):
                try:
                    ret = self.prox.nodes(instance.node).qemu(instance.id).firewall.ipset(f"ipfilter-net{i}").get()
                    
                    for r in ret: 
                        self.prox.nodes(instance.node).qemu(instance.id).firewall.ipset(f"ipfilter-net{i}/{r['cidr']}").delete()

                    self.prox.nodes(instance.node).qemu(instance.id).firewall.ipset(f"ipfilter-net{i}").delete()
                except Exception as e:
                    logger.info("Exception triggered while trying to recreate ipset, probably doesn't exist already", e=e, exc_info=True)

                logger.info(str(instance.metadata.network.nic_allocation.addresses[i]))
                self.prox.nodes(instance.node).qemu(instance.id).firewall.ipset.post(
                    name=f"ipfilter-net{i}"
                )

                self.prox.nodes(instance.node).qemu(instance.id).firewall.ipset(f"ipfilter-net{i}").post(
                    cidr=instance.metadata.network.nic_allocation.addresses[i].ip
                )

            self.prox.nodes(instance.node).qemu(f"{instance.id}/status/start").post()


    def stop_instance(
        self,
        instance: models.proxmox.Instance
    ):
        if instance.status == models.proxmox.Status.Running:
            if instance.type == models.proxmox.Type.LXC:
                self.prox.nodes(instance.node).lxc(f"{instance.id}/status/stop").post()
            elif instance.type == models.proxmox.Type.VPS:
                self.prox.nodes(instance.node).qemu(f"{instance.id}/status/stop").post()

    def shutdown_instance(
        self,
        instance: models.proxmox.Instance
    ):
        if instance.status == models.proxmox.Status.Running:
            if instance.type == models.proxmox.Type.LXC:
                self.prox.nodes(instance.node).lxc(f"{instance.id}/status/shutdown").post()
            elif instance.type == models.proxmox.Type.VPS:
                self.prox.nodes(instance.node).qemu(f"{instance.id}/status/shutdown").post()

    def mark_instance_active(
        self,
        instance: models.proxmox.Instance
    ): 
        # reset inactivity status, this resets tracking of the emails too
        instance.metadata.inactivity = models.proxmox.Inactivity(
            marked_active_at = datetime.date.today()
        )
        self.write_out_instance_metadata(instance)

    def add_instance_vhost(
        self,
        instance: models.proxmox.Instance,
        vhost: str,
        options: models.proxmox.VHostOptions
    ):
        instance.metadata.network.vhosts[vhost] = options
        self.write_out_instance_metadata(instance)

    def remove_instance_vhost(
        self,
        instance: models.proxmox.Instance,
        vhost: str
    ):
        if vhost in instance.metadata.network.vhosts:
            del instance.metadata.network.vhosts[vhost]

            self.write_out_instance_metadata(instance)
        else:
            raise exceptions.resource.NotFound(f"Could not find {vhost} vhost on instance")

    def get_port_forward_map(
        self
    ) -> Dict[int,Tuple[str, ipaddress.IPv4Address, int]]:
        instances = self.read_instances()

        port_map = {}

        for fqdn, instance in instances.items():

            for external_port, internal_port in instance.metadata.network.ports.items():
                if external_port in port_map:
                    logger.warning(f"warning, conflicting port map: {instance.fqdn} tried to map {external_port} but it's already taken!")
                    continue

                if config.proxmox.network.port_forward.range[0] > external_port or external_port > config.proxmox.network.port_forward.range[1]:
                    logger.warning(f"warning, port out of range: {instance.fqdn} tried to map {external_port} but it's out of range!")
                    continue
                
                port_map[external_port] = (instance.fqdn, instance.metadata.network.nic_allocation.addresses[0].ip, internal_port)
        
        return port_map

    def get_random_available_external_port(
        self
    ) -> Optional[int]:
        port_map = self.get_port_forward_map()

        occupied_set = set(port_map.keys())
        full_range_set = set(range(config.proxmox.network.port_forward.range[0],config.proxmox.network.port_forward.range[1]+1))

        remaining = full_range_set-occupied_set

        if len(remaining) > 0:
            return random.choice(tuple(remaining))
        
        raise exceptions.resource.Unavailable("out of suitable external ports")


    def validate_domain(
        self,
        instance: models.proxmox.Instance,
        domain: str
    ) -> (bool, Optional[List[str]]):
        """
        Verifies a single domain, if the domain is valid, (True, None) is returned
        If the domain is invalid, (False, a list of remarks is returned)

        We allow the instance fqdn as a domain, so if the FQDN == domain 
        i.e. <hostname>.<owner_username>.<base_fqdn_for_this_instance_type> / server1.ocanty.vps.netsoc.cloud
        You will _need_ to blacklist accounts that have the same subdomain as instance fqdn i.e 'vps' and 'container'

        We also allow users to use <username>.<base_domain>, i.e ocanty.netsoc.cloud or
        make use of a subdomain like <subdomain>.<username>.<base_domain>
        i.e blog.ocanty.netsoc.cloud
        """
        username = instance.metadata.owner

        txt_name = config.proxmox.network.vhosts.user_supplied.verification_txt_name
        txt_content = username

        base_domain = config.proxmox.network.vhosts.base_domain
        allowed_a_aaaa = config.proxmox.network.vhosts.user_supplied.allowed_a_aaaa

        split = domain.split(".")

        remarks = []

        # Allow fqdn
        if domain == instance.fqdn:
            return (True, None)

        # Ban any domain that tries to use the base fqdn that isn't the fqdn
        if instance.type == models.proxmox.Type.LXC and domain.endswith(config.proxmox.lxc.base_fqdn):
            return (False, [f"Invalid domain {domain}: only {instance.fqdn} is allowed to be used when domain ends with {config.proxmox.lxc.base_fqdn}"])
        elif instance.type == models.proxmox.Type.VPS and domain.endswith(config.proxmox.vps.base_fqdn):
            return (False, [f"Invalid domain {domain}: only {instance.fqdn} is allowed to be used when domain ends with {config.proxmox.vps.base_fqdn}"])

        # *.netsoc.cloud etc
        if domain.endswith(f".{base_domain}"):
            # the stuff at the start, i.e if they specified blog.ocanty.netsoc.co
            # prefix is blog.ocanty
            prefix = domain[:-len(f".{base_domain}")]
            split_prefix = prefix.split(".")
            
            # extract last part, i.e blog.ocanty => ocanty
            if split_prefix[-1] == username:
                # Valid domain
                return (True, None)
            else:
                remarks.append(f"Invalid domain {domain}: subdomain {split_prefix[-1]} is invalid, must be the same as username {username}")
        else: # custom domain
            try:
                info_list = socket.getaddrinfo(domain, 80)
            except Exception as e:
                remarks.append("Could not verify custom domain: {e}")

            a_aaaa = set(map(lambda info: info[4][0], filter(lambda x: x[0] in [socket.AddressFamily.AF_INET, socket.AddressFamily.AF_INET6], info_list)))
            
            if len(a_aaaa) == 0:
                remarks.append(f"Invalid domain {domain}: no A or AAAA records present")

            for record in a_aaaa:
                if record not in allowed_a_aaaa:
                    remarks.append(f"Invalid domain {domain}: unknown A/AAAA record ({record}), must be one of {allowed_a_aaaa}")

            # we need to check if they have the appropiate TXT record with the correct value
            custom_base = f"{split[len(split)-2]}.{split[len(split)-1]}"

            # check for _netsoc.theirdomain.com 
            try:
                q = dns.resolver.resolve(f"{txt_name}.{custom_base}", 'TXT')

                # dnspython returns the TXT record value enclosed in quotation marks
                # we will need to remove these
                txt_res = set(map(lambda x: str(x).strip('"'),q))

                if txt_content not in txt_res:
                    remarks.append(f"Invalid domain {domain}: could not find TXT record {txt_name} ({txt_name}.{custom_base}) set to {txt_content}, instead found {txt_res}!")
            except dns.resolver.NXDOMAIN:
                remarks.append(f"Invalid domain {domain}: could not find TXT record {txt_name} ({txt_name}.{custom_base}) set to {txt_content}")
            except dns.exception.DNSException as e:
                remarks.append(f"Invalid domain {domain}: unable to lookup record ({txt_name}.{custom_base}): ({e})")
            except Exception as e:
                remarks.append(f"Invalid domain {domain}: error {e} (contact SysAdmins)")

        if len(remarks) == 0:
            return (True, None)
        
        return (False, remarks)

    def get_vhost_forward_map(
        self,

    ) -> Dict[str, ipaddress.IPv4Address]:
        vhost_map = {}

        for fqdn, lxc in lxcs:
            ip = lxc.metadata.network.nic_allocation.addresses[0]

            for domain in lxc.metadata.network.vhosts:
                logger.warning(f"warning, conflicting port map: {lxc.fqdn} tried to map {external_port} but it's already taken!")

        return port_map

    def add_instance_port(
        self,
        instance: models.proxmox.Instance,
        external: int,
        internal: int
    ):
        port_map = self.get_port_forward_map()

        if external in port_map:
            raise exceptions.resource.Unavailable(f"Cannot map port {external} to {internal}, this port is currently taken by another user/another one of your instances")
            
        instance.metadata.network.ports[external] = internal
        self.write_out_instance_metadata(instance)

    def remove_instance_port(
        self, 
        instance: models.proxmox.Instance,
        external: int
    ):
        if external in instance.metadata.network.ports:
            del instance.metadata.network.ports[external]

        self.write_out_instance_metadata(instance)

    def build_traefik_config(
        self,
        web_entrypoints: List[str]
    ) -> dict:
        # Traefik does not like keys with empty values
        # so we gotta omit them by checking if the base key is already in the dict everywhere

        config = {}

        services = {}
        routers = {}

        for fqdn, instance in self.read_instances(ignore_errors=True).items():
            fqdn_prefix = fqdn.replace('.', '-')

            # first do vhosts
            for vhost, options in instance.metadata.network.vhosts.items():
                valid, remarks = self.validate_domain(instance, vhost)
                
                vhost_suffix = vhost.replace('.', '-')

                if valid is True:
                    if 'http' not in config:
                        config['http'] = {
                            'routers': {},
                            'services': {}
                        }
                    
                    config['http']['routers'][f"{fqdn_prefix}-{vhost_suffix}"] = {
                        "entrypoints": web_entrypoints,
                        "rule": f"Host(`{vhost}`)",
                        "service": f"{fqdn_prefix}-{vhost_suffix}",
                        "tls": {
                            "certResolver": "letsencrypt"
                        }
                    }

                    proto = "http"

                    if options.https is True:
                        proto = "https"

                    config['http']['services'][f"{fqdn_prefix}-{vhost_suffix}"] = {
                        "loadBalancer": {
                            "servers": [{ 
                                "url": f"{ proto }://{instance.metadata.network.nic_allocation.addresses[0].ip}:{ options.port }"
                            }]
                        }
                    }


        # then do tcp/udp port mappings
        for external_port, internal_tuple in self.get_port_forward_map().items():
            fqdn, ip, internal_port = internal_tuple
            fqdn_prefix = fqdn.replace('.', '-')
            
            if 'tcp' not in config and 'udp' not in config:
                config['tcp'] = {
                    'routers': {},
                    'services': {}
                }

                config['udp'] = {
                    'routers': {},
                    'services': {}
                }

            config['tcp']['routers'][f"{fqdn_prefix}-{external_port}-tcp"] = {
                "entryPoints": [f"netsoc-cloud-{external_port}-tcp"],
                "rule": "HostSNI(`*`)",
                "service": f"{fqdn_prefix}-{external_port}-tcp"
            }

            config['tcp']['services'][f"{fqdn_prefix}-{external_port}-tcp"] = {
                "loadBalancer": {
                    "servers": [{
                        "address": f"{ip}:{internal_port}"
                    }]
                }
            }

            config['udp']['routers'] [f"{fqdn_prefix}-{external_port}-udp"] = {
                "entryPoints": [f"netsoc-cloud-{external_port}-udp"],
                "service": f"{fqdn_prefix}-{external_port}-udp"
            }

            config['udp']['services'] [f"{fqdn_prefix}-{external_port}-udp"] = {
                "loadBalancer": {
                    "servers": [{
                        "address": f"{ip}:{internal_port}"
                    }]
                }
            }
            

        return config
