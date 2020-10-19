
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
        if instance_type == models.proxmox.Type.LXC:
            network = config.proxmox.lxc.network.network
            base_ip = config.proxmox.lxc.network.ip
            gateway = base_ip + 1
        elif instance_type == models.proxmox.Type.VPS:
            network = config.proxmox.vps.network.network
            base_ip = config.proxmox.vps.network.ip
            gateway = base_ip + 1

        # returns set with network and broadcast address removed
        ips = set(network.hosts())

        # remove router/gateway address
        ips.remove(gateway)

        # remove any addresses assigned to any of the lxcs
        for fqdn, instance in self.read_instances(instance_type).items():
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
                macaddress="02:00:00:%02x:%02x:%02x" % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            )
        else:
            raise exception.resource.Unavailable("Could not allocate an IP for the instance. No IPs available")

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
            self.prox.nodes(instance.node).lxc(f"{instance.id}/config").put(description=yaml_description)
        elif instance.type == models.proxmox.Type.VPS:
            self.prox.nodes(instance.node).qemu(f"{instance.id}/config").put(description=yaml_description)

    def create_instance(
        self,
        instance_type: models.proxmox.Type,
        account: models.account.Account,
        hostname: str,
        request_detail: models.proxmox.RequestDetail
    ) -> Tuple[str,str]:

        template = self.get_template(instance_type, request_detail.template_id)

        try:
            existing_vm = self.read_instance_by_account(instance_type, account, hostname)
            raise exceptions.resource.AlreadyExists(f"Instance {hostname} already exists")
        except exceptions.resource.NotFound:
            pass

        node_name = self._select_best_node(template.specs)
        fqdn = self._get_instance_fqdn_for_account(instance_type, account, hostname)

        if instance_type == models.proxmox.Type.LXC:
            if template.disk_format != models.proxmox.Template.DiskFormat.TarGZ:
                raise exceptions.resource.Unavailable(f"Template (on LXC) {detail.template_id} must use TarGZ of RootFS format!")

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

            user_ssh_public_key, user_ssh_private_key = utilities.auth.generate_rsa_public_private_ssh_key_pair()
            mgmt_ssh_public_key, mgmt_ssh_private_key = utilities.auth.generate_rsa_public_private_ssh_key_pair()
            password = self._random_password()

            metadata = models.proxmox.Metadata(
                owner=account.username,
                request_detail=request_detail,
                inactivity=models.proxmox.Inactivity(
                    marked_active_at=datetime.date.today()
                ),
                network=models.proxmox.Network(
                    nic_allocation=self._allocate_nic(instance_type)
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
                "ssh-public-keys": f"{user_ssh_public_key}\n{mgmt_ssh_public_key}",
                "nameserver": "1.1.1.1",
                "net0": f"rate=100,name=eth0,bridge={config.proxmox.lxc.bridge},tag={config.proxmox.lxc.vlan},hwaddr={metadata.network.nic_allocation.macaddress},ip={metadata.network.nic_allocation.addresses[0]},mtu=1450"
            })

            self._wait_vmid_lock(instance_type, node_name, hash_id)
            
            # if there is an id collision, proxmox will do id+1, so we need to search for the lxc again
            lxc = self._read_instance_by_fqdn(instance_type, fqdn)

            self.prox.nodes(lxc.node).lxc(f"{lxc.id}/resize").put(
                disk='rootfs',
                size=f'{template.specs.disk_space}G'
            )

            self._wait_vmid_lock(instance_type, node_name, lxc.id)

            return password, user_ssh_private_key
        elif instance_type == models.proxmox.Type.VPS:
            download_images_path = self.prox.storage(config.proxmox.lxc.dir_pool).get()['path'] + "/template/qcow2"
            vms_image_path = f"/tmp/admin-api/{vm.metadata.provision.image.disk_sha256sum}"
            download_path = f"{images_path}/{socket.gethostname()}-{os.getpid()}-{vm.metadata.provision.image.disk_sha256sum}"

            with ProxmoxNodeSSH(vm.node) as con:
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"mkdir -p {images_path}"
                )
                status = stdout.channel.recv_exit_status()

                if status != 0:
                    provision_failed(f"Could not download image: could not reserve download dir")

                # See if the image exists
                try:
                    con.sftp.stat(image_path)

                    # Checksum image    
                    stdin, stdout, stderr = con.ssh.exec_command(
                        f"sha256sum {image_path} | cut -f 1 -d' '"
                    )

                    if vm.metadata.provision.image.disk_sha256sum not in str(stdout.read()):
                        provision_failed(f"Downloaded image does not pass SHA256SUMS given {status}: {stderr.read()} {stdout.read()}")

                except FileNotFoundError as e:
                    provision_stage(models.proxmox.Provision.Stage.DownloadImage)

                    # Original image does not exist, we gotta download it
                    stdin, stdout, stderr = con.ssh.exec_command(
                        f"wget {vm.metadata.provision.image.disk_url} -O {download_path}"
                    )
                    status = stdout.channel.recv_exit_status()

                    if status != 0:
                        provision_failed(f"Could not download image: error {status}: {stderr.read()} {stdout.read()}")

                    # Checksum image    
                    stdin, stdout, stderr = con.ssh.exec_command(
                        f"sha256sum {download_path} | cut -f 1 -d' '"
                    )

                    if vm.metadata.provision.image.disk_sha256sum not in str(stdout.read()):
                        provision_failed(f"Downloaded image does not pass SHA256SUM given {status}: {stderr.read()} {stdout.read()}")

                    # Move image
                    stdin, stdout, stderr = con.ssh.exec_command(
                        f"rm -rf {image_path} && mv {download_path} {image_path}"
                    )

                    status = stdout.channel.recv_exit_status()
                    if status != 0:
                        provision_failed(f"Couldn't rename VM image {status}: {stderr.read()} {stdout.read()}")
                
                provision_stage(models.proxmox.Provision.Stage.FlashImage)

                # Images path for installed VMs
                vms_images_path = self.prox.storage(config.proxmox.uservm.dir_pool).get()['path'] + "/images"

                # Move disk image
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"cd {vms_images_path} && rm -rf {vm.id} && mkdir {vm.id} && cd {vm.id} && cp {image_path} ./primary.{ vm.metadata.provision.image.disk_format }"
                )
                status = stdout.channel.recv_exit_status()
                
                if status != 0:
                    provision_failed(f"Couldn't copy VM image {status}: {stderr.read()} {stdout.read()}")

                # Create disk for EFI
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"cd {vms_images_path}/{vm.id} && qemu-img create -f qcow2 efi.qcow2 128K"
                )
                status = stdout.channel.recv_exit_status()
                
                if status != 0:
                    provision_failed(f"Couldn't create EFI image {status}: {stderr.read()} {stdout.read()}")

                self.prox.nodes(vm.node).qemu(f"{vm.id}/config").put(
                    virtio0=f"{config.proxmox.uservm.dir_pool}:{vm.id}/primary.{ vm.metadata.provision.image.disk_format }",
                    cores=vm.metadata.provision.image.specs.cores,
                    memory=vm.metadata.provision.image.specs.memory,
                    bios='ovmf',
                    efidisk0=f"{config.proxmox.uservm.dir_pool}:{vm.id}/efi.qcow2",
                    scsihw='virtio-scsi-pci',
                    machine='q35',
                    serial0='socket',
                    bootdisk='virtio0'
                )

                self.prox.nodes(vm.node).qemu(f"{vm.id}/resize").put(
                    disk='virtio0',
                    size=f'{vm.metadata.provision.image.specs.disk_space}G'
                )

    def delete_instance(
        self,
        instance: models.proxmox.Instance
    ):
        if instance.status != models.proxmox.Status.Stopped:
            raise exceptions.resource.Unavailable("Cannot delete instance, instance is running")

        if instance.type == models.proxmox.Type.LXC:
            self.prox.nodes(instance.node).lxc(f"{instance.id}").delete()
        elif instance_type == models.proxmox.Type.VPS:
            # delete cloud-init data
            with ProxmoxNodeSSH(instance.node) as con:
                snippets_path = self.prox.storage(config.proxmox.vps.dir_pool).get()['path'] + "/snippets"

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
                res = self.prox.nodes(node_name).lxc(f"{vm_id}/config").get()

            now = time.time()

            if 'lock' not in res: 
                break

            if (now-start) > timeout:
                raise exceptions.resource.Unavailable("Timeout occured waiting for VPS/LXC to unlock.")

            time.sleep(poll_interval)


    def _read_instance_on_node(
        self,
        instance_type: models.proxmox.Type,
        node: str,
        vmid: int
    ) -> models.proxmox.Instance:

        if instance_type == models.proxmox.Type.LXC:
            try:
                lxc_config = self.prox.nodes(node).lxc.get(f"{vmid}/config")
            except Exception as e:
                raise exceptions.resource.NotFound("The LXC does not exist")

            # proxmox uses hostname as the lxc name
            # but name for vm name, god help me
            fqdn = lxc_config['hostname']

            # decode description
            try:
                metadata = models.proxmox.Metadata.parse_obj(
                    yaml.safe_load(lxc_config['description'])
                )
            except Exception as e:
                raise exceptions.resource.Unavailable(
                    f"LXC is unavailable, malformed metadata description: {e}"
                )

            # for user ocanty, returns .ocanty.lxc.cloud.netsoc.co
            suffix = self._get_instance_fqdn_for_username(instance_type, metadata.owner, "")

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

            current_status = self.prox.nodes(node).lxc.get(f"{vmid}/status/current")
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
                specs=specs,
                remarks=[],
                status=status,
                active=active
            )

            # Build remarks about the thing, problems, etc...
            for vhost in instance.metadata.network.vhosts:
                valid, remarks = self.validate_domain(instance.metadata.owner, vhost)

                if valid is not True:
                    instance.remarks += remarks

            return instance
        elif instance_type == models.proxmox.Type.VPS:
            try:
                vm_config = self.prox.nodes(node).qemu.get(f"{vmid}/config")
            except Exception as e:
                raise exceptions.resource.NotFound("The instance does not exist")

            fqdn = vm_config['name']
            
            # decode description
            try:
                metadata = models.proxmox.Metadata.parse_obj(
                    yaml.safe_load(vm_config['description'])
                )
            except Exception as e:
                raise exceptions.resource.Unavailable(
                    f"Instance is unavailable, malformed metadata description: {e}"
                )

            # for user ocanty, returns .ocanty.uservm.netsoc.co
            suffix = self._get_instance_fqdn_for_username(instance_type, metadata.owner, "")

            # trim suffix
            if not fqdn.endswith(suffix):
                raise exceptions.resource.Unavailable(
                    f"Found Instance but Owner / FQDN do not align, FQDN is {fqdn} but owner is {metadata.owner}"
                )

            hostname = fqdn[:-len(suffix)]

            if (datetime.date.today() - metadata.inactivity.marked_active_at).days > config.proxmox.uservm.inactivity_shutdown_num_days:
                active = False
            else:
                active = True 

            # config str looks like this: whatever,size=30G
            # extract the size str
            size_str = dict(map(lambda x: (x.split('=') + [""])[:2], vm_config['virtio0'].split(',')))['size']

            disk_space = int(size_str[:-1])

            specs = models.proxmox.Specs(
                cores=vm_config['cores'],
                memory=vm_config['memory'],
                swap=vm_config['swap'],
                disk_space=disk_space
            )

            current_status = self.prox.nodes(node).qemu.get(f"{vmid}/status/current")
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
                specs=specs,
                remarks=[],
                status=status,
                active=active
            )

            # Build remarks about the thing, problems, etc...
            for vhost in instance.metadata.network.vhosts:
                valid, remarks = self.validate_domain(instance.metadata.owner, vhost)

                if valid is not True:
                    instance.remarks += remarks

            return instance

        raise exceptions.resource.NotFound("The instance does not exist")

    def _read_instance_by_fqdn(
        self,
        instance_type: models.proxmox.Type,
        fqdn: str
    ) -> models.proxmox.Instance:
        if instance_type == models.proxmox.Type.LXC:
            for node in self.prox.nodes().get():
                for potential in self.prox.nodes(node['node']).lxc.get():
                    # is it an one of our lxc fqdns?
                    if potential['name'] == fqdn:
                        instance = self._read_instance_on_node(instance_type, node['node'], potential['vmid'])
                        return instance

        elif instance_type == models.proxmox.Type.VPS:
            for node in self.prox.nodes().get():
                for potential in self.prox.nodes(node['node']).qemu.get():
                    if potential['name'] == fqdn:
                        instance = self._read_instance_on_node(instance_type, node['node'], potential['vmid'])
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
        account: models.account.Account
    ) -> Dict[str, models.proxmox.Instance]:
        """Returns a dict indexed by hostname of uservms owned by user account"""
        if instance_type == models.proxmox.Type.LXC:
            ret = { }
            
            for node in self.prox.nodes().get():
                for lxc_dict in self.prox.nodes(node['node']).lxc.get():
                    if lxc_dict['name'].endswith(self._get_instance_fqdn_for_account(instance_type, account, "")):
                        lxc = self._read_instance_on_node(instance_type, node['node'], lxc_dict['vmid'])
                        ret[lxc.hostname] = lxc
                        
            
            return ret
        elif instance_type == models.proxmox.Type.VPS:
            ret = { }
            
            for node in self.prox.nodes().get():
                for vps_dict in self.prox.nodes(node['node']).qemu.get():
                    if vps_dict['name'].endswith(self._get_instance_fqdn_for_account(instance_type, account, "")):
                        vps = self._read_instance_on_node(instance_type, node['node'], vps_dict['vmid'])
                        ret[vps.hostname] = vps
                        
            
            return ret

    def read_instances(
        self,
        instance_type: Optional[models.proxmox.Type] = None
    ) -> Dict[str, models.proxmox.Instance]:
        if instance_type == models.proxmox.Type.LXC:
            ret = {}

            for node in self.prox.nodes().get():
                for lxc_dict in self.prox.nodes(node['node']).lxc.get():
                    if lxc_dict['name'].endswith(config.proxmox.lxc.base_fqdn):
                        lxc = self._read_instance_on_node(instance_type, node['node'], lxc_dict['vmid'])
                        ret[lxc.fqdn] = lxc

            return ret  
        elif instance_type == models.proxmox.Type.VPS:
            ret = {}

            for node in self.prox.nodes().get():
                for vps_dict in self.prox.nodes(node['node']).vps.get():
                    if vps_dict['name'].endswith(config.proxmox.vps.base_fqdn):
                        vps = self._read_instance_on_node(instance_type, node['node'], vps_dict['vmid'])
                        ret[vps.fqdn] = vps

            return ret  
        elif instance_type == None:
            lxcs = self.read_instances(models.proxmox.Type.LXC)
            vpses = self.read_instances(models.proxmox.Type.VPS)
            
            return {**lxcs, **vpses}


    def reset_instance_root_user(
        self,
        instance: models.proxmox.Instance
    ) -> Tuple[str, str]:
        """Returns a tuple of password, private_key"""
        user_ssh_public_key, user_ssh_private_key = utilities.auth.generate_rsa_public_private_ssh_key_pair()
        mgmt_ssh_public_key, mgmt_ssh_private_key = utilities.auth.generate_rsa_public_private_ssh_key_pair()

        password = self._random_password()

        root_user = models.proxmox.RootUser(
            password_hash=self._hash_password(password),
            ssh_public_key=user_ssh_public_key,
            mgmt_ssh_public_key=mgmt_ssh_public_key,
            mgmt_ssh_private_key=mgmt_ssh_private_key
        )

        if instance.type == models.proxmox.Type.LXC:
            if instance.status == models.proxmox.Status.Stopped:
                raise exceptions.resource.Unavailable("The instance must be running to reset the root password")

            with ProxmoxNodeSSH(instance.node) as con:
                escaped_hash = root_user.password_hash.replace('$','$')
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"echo -e 'root:{escaped_hash}' | pct exec {instance.id} -- chpasswd -e"
                )
                status = stdout.channel.recv_exit_status()

                if status != 0:
                    raise exceptions.resource.Unavailable(
                        f"Could not start instance: unable to set root password: {status}: {stdout.read()} {stderr.read()}"
                    )

                stdin, stdout, stderr = con.ssh.exec_command(
                    f"echo -e '# --- BEGIN PVE ---\\n{root_user.ssh_public_key}\\n{root_user.mgmt_ssh_public_key}\\n# --- END PVE ---' | pct push { instance.id } /dev/stdin '/root/.ssh/authorized_keys' --perms 0600 --user 0 --group 0"
                )
                status = stdout.channel.recv_exit_status()

                if status != 0:
                    raise exceptions.resource.Unavailable(
                        f"Could not start LXC: unable to inject ssh keys {status}: {stdout.read()} {stderr.read()}"
                    )

            instance.metadata.root_user = root_user
            self.write_out_instance_metadata(instance)

        elif instance.type == models.proxmox.Type.VPS:
            if instance.status == models.proxmox.Status.Started:
                # VPS needs to be stopped because we set the root pw using cloudinit on boot
                raise exceptions.resource.Unavailable("The instance must be stopped to reset the root password")

            instance.metadata.root_user = root_user
            self.write_out_instance_metadata(instance)    

            # rerun cloudinit - will write ssh keys and root pass
            self.start_instance(instance, vps_rerun_cloudinit=True)

        return password, user_ssh_private_key

    def start_instance(
        self,
        instance: models.proxmox.Instance,
        vps_rerun_cloudinit: Optional[bool] = False
    ):
        if instance.status != models.proxmox.Status.Running:
            if instance.type == models.proxmox.Type.LXC:
                self.prox.nodes(instance.node).lxc(f"{instance.id}/config").put(**{
                    "nameserver": "1.1.1.1",
                    "net0": f"rate=100,name=eth0,bridge={config.proxmox.lxc.bridge},tag={config.proxmox.lxc.vlan},hwaddr={instance.metadata.network.nic_allocation.macaddress},ip={instance.metadata.network.nic_allocation.addresses[0]},mtu=1450",
                })

                self.prox.nodes(instance.node).lxc(f"{instance.id}/status/start").post()
            elif instance.type == models.proxmox.Type.VPS:

                # Detach existing cloud-init drive (if any)
                self.prox.nodes(instance.node).qemu(f"{instance.id}/config").put(
                    ide2="none,media=cdrom",
                    cicustom=""
                )

                # install cloud-init data
                with ProxmoxNodeSSH(vm.node) as con:
                    snippets_path = self.prox.storage(config.proxmox.vps.dir_pool).get()['path'] + "/snippets"

                    con.sftp.putfo(
                        io.StringIO(""),
                        f'{ snippets_path }/{instance.fqdn}.metadata.yml'
                    )

                    userdata_config = f"""#cloud-config
preserve_hostname: false
manage_etc_hosts: true
fqdn: { instance.fqdn }
ssh_pwauth: 1
disable_root: 0
packages:
    - qemu-guest-agent
runcmd:
    - [ systemctl, enable, qemu-guest-agent ]
    - [ systemctl, start, qemu-guest-agent, --no-block ]  
users:
    -   name: root
        lock_passwd: false
        shell: /bin/bash
        ssh_redirect_user: false
        ssh_authorized_keys:
            - { instance.metadata.root_user.ssh_public_key }
            - { instance.metadata.root_user.mgmt_ssh_public_key }
chpasswd:
    list: |
        root:{ instance.metadata.root_user.password_hash }
    expire: false
"""

                    if vps_rerun_cloudinit == True:
                        # This will wipe previous cloud-init state from previous boots
                        # will re run all cloudinit_initial_modules, i.e reapplying user info and networking
                        # this typically only happens when a password reset has been requested
                        userdata_config += """
bootcmd: 
    - rm -f /etc/netplan/50-cloud-init.yml
    - cloud-init clean --logs
"""         

                    con.sftp.putfo(
                        io.StringIO(userdata_config),
                        f'{ snippets_path }/{instance.fqdn}.userdata.yml'
                    )

                    con.sftp.putfo(
                        io.StringIO(f"""
ethernets:
    net0:
        match:
            macaddress: { instance.metadata.network.nic_allocation.macaddress }
        nameservers:
            addresses:
                - 1.1.1.1
                - 8.8.8.8
        gateway4: { config.proxmox.uservm.network.ip + 1 }
        optional: true
        addresses:
            - { instance.metadata.network.nic_allocation.addresses[0] }
        mtu: 1450 
version: 2
                        """),
                        f'{ snippets_path }/{instance.fqdn}.networkconfig.yml'
                    )

                # Insert cloud-init stuff
                self.prox.nodes(instance.node).qemu(f"{instance.id}/config").put(
                    cicustom=f"user={ config.proxmox.vps.dir_pool }:snippets/{instance.fqdn}.userdata.yml,network={ config.proxmox.vps.dir_pool }:snippets/{instance.fqdn}.networkconfig.yml,meta={ config.proxmox.vps.dir_pool }:snippets/{instance.fqdn}.metadata.yml",
                    ide2=f"{ config.proxmox.vps.dir_pool }:cloudinit,format=qcow2"
                )

                # Set network card
                self.prox.nodes(instance.node).qemu(f"{instance.id}/config").put(
                    net0=f"virtio={ instance.metadata.network.nic_allocation.macaddress },bridge={config.proxmox.vps.bridge},tag={config.proxmox.vps.vlan}"
                )

                self.prox.nodes(instance.node).qemu(f"{vm.id}/status/start").post()


    def stop_instance(
        self,
        instance: models.proxmox.Instance
    ):
        if instance.status == models.proxmox.Status.Running:
            if instance.type == models.proxmox.Type.LXC:
                self.prox.nodes(instance.node).lxc(f"{instance.id}/status/stop").post()
            elif instance.type == models.proxmox.Type.VPS:
                self.prox.nodes(instance.node).qemu(f"{instance.id}/status/stop").post()

                # delete cloud-init data
                with ProxmoxNodeSSH(instance.node) as con:
                    snippets_path = self.prox.storage(config.proxmox.vps.dir_pool).get()['path'] + "/snippets"

                    stdin, stdout, stderr = con.ssh.exec_command(
                        f"rm -f '{ snippets_path }/{instance.fqdn}.networkconfig.yml' '{ snippets_path }/{instance.fqdn}.userdata.yml' '{ snippets_path }/{instance.fqdn}.metadata.yml'"
                    )

                # Detach existing cloud-init drive (if any)
                self.prox.nodes(instance.node).qemu(f"{instance.id}/config").put(
                    ide2="none,media=cdrom",
                    cicustom=""
                )


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
    ) -> Dict[int,Tuple[ipaddress.IPv4Interface, int]]:
        instances = self.read_instances()

        port_map = {}

        for fqdn, instance in instances.items():
            ip = instance.metadata.network.nic_allocation.addresses[0]

            for external_port, internal_port in instance.metadata.network.ports.items():
                if external_port in port_map:
                    logger.warning(f"warning, conflicting port map: {instance.fqdn} tried to map {external_port} but it's already taken!")
                    continue

                if config.proxmox.port_forward.range[0] > external_port or external_port > config.proxmox.port_forward.range[1]:
                    logger.warning(f"warning, port out of range: {instance.fqdn} tried to map {external_port} but it's out of range!")
                    continue
                
                port_map[external_port] = (ip, internal_port)
        
        return port_map

    def validate_domain(
        self,
        username: models.account.Username,
        domain: str
    ) -> (bool, Optional[List[str]]):
        """
        Verifies a single domain, if the domain is valid, None is returned
        If the domain is invalid, a list of remarks is returned
        """
        txt_name = config.proxmox.vhosts.user_supplied.verification_txt_name
        txt_content = username

        base_domain = config.proxmox.vhosts.netsoc_supplied.base_domain
        allowed_a_aaaa = config.proxmox.vhosts.user_supplied.allowed_a_aaaa

        split = domain.split(".")

        remarks = []
            
        # *.netsoc.co etc
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
                remarks.append(f"Domain {domain} - subdomain {split_prefix[:len(split_prefix)-1]} must end with one of {username}.{base_domain}")
        else: # custom domain
            try:
                info_list = socket.getaddrinfo(domain, 80)
            except Exception as e:
                remarks.append("Could not verify custom domain: {e}")

            a_aaaa = set(map(lambda info: info[4][0], filter(lambda x: x[0] in [socket.AddressFamily.AF_INET, socket.AddressFamily.AF_INET6], info_list)))
            
            if len(a_aaaa) == 0:
                remarks.append(f"Domain {domain} - no A or AAAA records present")

            for record in a_aaaa:
                if record not in allowed_a_aaaa:
                    remarks.append(f"Domain {domain} - unknown A/AAAA record on domain ({record}), must be one of {allowed_a_aaaa}")

            # we need to check if they have the appropiate TXT record with the correct value
            custom_base = f"{split[len(split)-2]}.{split[len(split)-1]}"

            # check for _netsoc.theirdomain.com 
            try:
                q = dns.resolver.resolve(f"{txt_name}.{custom_base}", 'TXT')

                # dnspython returns the TXT record value enclosed in quotation marks
                # we will need to remove these
                txt_res = set(map(lambda x: str(x).strip('"'),q))

                if txt_content not in txt_res:
                    remarks.append(f"Domain {domain} - could not find TXT record {txt_name} ({txt_name}.{custom_base}) set to {txt_content}, instead found {txt_res}!")
            except dns.resolver.NXDOMAIN:
                remarks.append(f"Domain {domain} - could not find TXT record {txt_name} ({txt_name}.{custom_base}) set to {txt_content}")
            except dns.exception.DNSException as e:
                remarks.append(f"Domain {domain} - unable to lookup record ({txt_name}.{custom_base}): ({e})")
            except Exception as e:
                remarks.append(f"Domain {domain} - error {e} (contact SysAdmins)")

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
        services = {}
        routers = {}

        for fqdn, instance in self.read_instances().items():
            for vhost, options in instance.metadata.network.vhosts.items():
                valid, remarks = self.validate_domain(instance.metadata.owner, vhost)

                if valid is True:
                    routers[f"{fqdn}[{vhost}]"] = {
                        "entrypoints": web_entrypoints,
                        "rule": f"Host(`{vhost}`)",
                        "service": f"{fqdn}[{vhost}]",
                        "tls": {
                            "certResolver": "letsencrypt"
                        }
                    }

                    proto = "http"

                    if options.https is True:
                        proto = "https"

                    services[f"{fqdn}[{vhost}]"] = {
                        "loadBalancer": {
                            "servers": [{ 
                                "url": f"{ proto }://{instance.metadata.network.nic_allocation.addresses[0].ip}:{ options.port }"
                            }]
                        }
                    }
    

        config = {
            "http": {
                "routers": routers,
                "services": services
            }
        }

        return config





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




