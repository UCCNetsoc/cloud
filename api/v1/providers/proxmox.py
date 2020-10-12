
import random
import yaml
import datetime
import requests
import hashlib
import os
import socket
import shutil
import paramiko
import ipaddress
import io
import crypt

import structlog as logging

from urllib.parse import urlparse, unquote

from typing import Optional, Tuple
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

    def _select_uservm_best_node(
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

    def _get_userlxc_fqdn_for_username(
        self,
        username: str,
        hostname: str
    ) -> str:
        return f"{hostname}.{username}.{config.proxmox.userlxc.base_fqdn}"

    def _get_userlxc_fqdn_for_account(
        self,
        account: models.account.Account,
        hostname: str
    ) -> str:
        """
        Returns a FQDN for a LXC hostname for an account

        i.e cake => cake.ocanty.userlxc.netsoc.co
        """
        return self._get_userlxc_fqdn_for_username(account.username, hostname)

    def _get_uservm_fqdn_for_username(
        self,
        username: str,
        hostname: str
    ) -> str:
        return f"{hostname}.{username}.{config.proxmox.uservm.base_fqdn}"

    def _get_uservm_fqdn_for_account(
        self,
        account: models.account.Account,
        hostname: str
    ) -> str:
        """
        Returns a FQDN for a VM hostname for an account

        i.e cake => cake.ocanty.uservm.netsoc.co
        """
        return self._get_uservm_fqdn_for_username(account.username, hostname)

    def _read_uservm_on_node(
        self,
        node: str,
        fqdn: str
    ) -> models.proxmox.UserVM:  
        """Find a VM on a node or throw an exception"""

        # get each vm on the node
        for vm_dict in self.prox.nodes(node).qemu.get():
            if vm_dict['name'] == fqdn:
                config = self.prox.nodes(node).qemu.get(f"{vm_dict['vmid']}/config")

                # decode description
                try:
                    logger.info(yaml.safe_load(config['description']))
                    metadata = models.proxmox.Metadata.parse_obj(
                        yaml.safe_load(config['description'])
                    )
                except Exception as e:
                    raise exceptions.resource.Unavailable(
                        f"User VM is unavailable, malformed metadata description: {e}"
                    )

                # for user ocanty, returns .ocanty.uservm.netsoc.co
                suffix = self._get_fqdn_for_username(metadata.owner, "")

                # trim suffix
                if not vm_dict['name'].endswith(suffix):
                    raise exceptions.resource.Unavailable(
                        f"Found VM but Owner / FQDN do not align, FQDN is {vm_dict['name']} but owner is {metadata.owner}"
                    )

                hostname = vm_dict['name'][:-len(suffix)]

                vm = models.proxmox.UserVM(
                    id=vm_dict['vmid'],
                    fqdn=fqdn,
                    hostname=hostname,
                    node=node,
                    metadata=metadata,
                    specs=metadata.provision.image.specs,
                    remarks=[],
                    status=models.proxmox.Status.NotApplicable
                )

                # if it's a vm request
                if metadata.provision.stage == models.proxmox.Provision.Stage.AwaitingApproval:
                    vm.remarks.append(
                        "Your VM is currently awaiting approval from the SysAdmins, you will receive an email once it has been approved"
                    )
                elif metadata.provision.stage == models.proxmox.Provision.Stage.Approved:
                    vm.remarks.append(
                        "Your VM has been approved, you can now install it"
                    )
                elif metadata.provision.stage == models.proxmox.Provision.Stage.Installed:
                    vm.specs=models.proxmox.Specs(
                        cores=config['cores'],
                        memory=config['memory'],
                        disk_space=0
                    ),

                    if 'virtio0' not in config:
                        vm.remarks.append("VM is missing its disk. Contact SysAdmins")
                    else:
                        # config str looks like this: local-lvm:vm-1867516-disk-0,backup=0,size=30G

                        # extract the size str
                        size_str = dict(map(lambda x: (x.split('=') + [""])[:2], config['virtio0'].split(',')))['size']

                        vm.specs.disk_space = int(size_str[:-1])
                else:
                    vm.remarks.append(
                        "Installation may take awhile, check back later"
                    )

                return vm

        raise exceptions.resource.NotFound("The VM does not exist")

    def _read_uservm_by_fqdn(
        self,
        fqdn: str
    ) -> models.proxmox.UserVM:
        """Find a VM in the cluster or throw an exception"""

        # Look on each node for the VM
        for node in self.prox.nodes().get():
            try:
                vm = self._read_uservm_on_node(node['node'], fqdn)
                return vm
            except exceptions.resource.NotFound:
                pass
        
        raise exceptions.resource.NotFound("The VM does not exist")

    def read_uservms_by_account(
        self,
        account: models.account.Account,
        hostname: str
    ) -> models.proxmox.UserVM:
        """Read a VM owned by an account"""
        return self._read_uservm_by_fqdn(self._get_fqdn_for_account(account, hostname))

    def _random_password(
        self
    ) -> str:
        return ''.join(random.choice(string.ascii + string.digits) for _ in range(16))

    def _hash_password(
        self,
        password: str
    ) -> str:
        return crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))

    def request_uservm(
        self,
        account: models.account.Account,
        hostname: str,
        image: models.proxmox.Image,
        reason: str
    ):
        try:
            existing_vm = self.read_by_account(account, hostname)
            raise exceptions.resource.AlreadyExists(f"VM {hostname} already exists")
        except exceptions.resource.NotFound as e:
            pass

        node_name = self._select_best_node(image.specs)
        fqdn = self._get_fqdn_for_account(account, hostname)

        # Allocate the VM on an IP address that is not the gateway, network or broadcast address
        # TODO - don't use random
        offset_ip = (config.proxmox.uservm.network.ip + 1) + random.randint(1,config.proxmox.uservm.network.network.num_addresses-3)
        assigned_ip_and_netmask = f"{offset_ip}/{config.proxmox.uservm.network.network.prefixlen}"

        nic_allocation=models.proxmox.NICAllocation(
            addresses=[
                ipaddress.IPv4Interface(assigned_ip_and_netmask)
            ],
            gateway4=config.proxmox.uservm.network.ip + 1, # router address is assumed to be .1 of the subnet
            macaddress="02:00:00:%02x:%02x:%02x" % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        )

        management_key = utilities.auth.generate_rsa_public_private_key_pair()

        logger.info(management_key)

        metadata = models.proxmox.Metadata(
            owner=account.username,
            provision=models.proxmox.Provision(
                image=image
            ),
            reason=reason,
            inactivity=models.proxmox.Inactivity(
                requested_at=datetime.date.today(),
                last_marked_active=datetime.date.today()
            ),
            network=models.proxmox.Network(
                ports=[],
                domains=[],
                nic_allocation=nic_allocation
            ),
            root_user=models.proxmox.RootUser(
                user_ssh_password_hash=self._hash_password(self._random_password()),
                management_ssh_public_key=management_key[0],
                management_ssh_private_key=management_key[1]
            )
        )

        # Store VM metadata in the description field
        # https://github.com/samuelcolvin/pydantic/issues/1043
        yaml_description = yaml.dump(yaml.safe_load(metadata.json()), default_flow_style=False)

        # reserve a VM, but don't set any of the specs yet
        # just setup the metadata we'll need later
        random.seed(f"{fqdn}-{node_name}")
        vm_hash_id = random.randint(1000, 5000000)
        random.seed()
        
        self.prox.nodes(f"{node_name}/qemu").post(**{
            'name': fqdn,
            'vmid': vm_hash_id,
            'description': yaml_description
        })

    def write_out_uservm_metadata(
        self,
        vm: models.proxmox.UserVM
    ):
        yaml_description = yaml.dump(yaml.safe_load(vm.metadata.json()), default_flow_style=False)
        
        # https://github.com/samuelcolvin/pydantic/issues/1043
        self.prox.nodes(vm.node).qemu(f"{vm.id}/config").post(description=yaml_description)

    def approve_uservm(
        self,
        vm: models.proxmox.UserVM
    ):  
        if vm.metadata.provision.stage == models.proxmox.Provision.Stage.AwaitingApproval:
            vm.metadata.provision.stage = models.proxmox.Provision.Stage.Approved

            self.write_out_metadata(vm)
    
    def uninstall_uservm(
        self,
        vm: models.proxmox.UserVM
    ):
        # Don't allow installations on unapproved VMs
        if vm.metadata.provision.stage == models.proxmox.Provision.Stage.AwaitingApproval:
            raise exceptions.resource.Unavailable("Cannot uninstall VM. VM requires approval")

        vm.metadata.provision.stage = models.proxmox.Provision.Stage.Approved
        vm.metadata.provision.remarks = []
        self.write_out_metadata(vm)

    def install_uservm(
        self,
        vm: models.proxmox.UserVM
    ):
        # Don't allow installations on unapproved VMs
        if vm.metadata.provision.stage == models.proxmox.Provision.Stage.AwaitingApproval:
            raise exceptions.resource.Unavailable("Cannot install VM. VM requires approval")
        
        if vm.metadata.provision.stage == models.proxmox.Provision.Stage.Failed:
            raise exceptions.resource.Unavailable("Cannot install VM. Uninstall VM ")

        # # Approved is the base "approved but not installed" state
        if vm.metadata.provision.stage != models.proxmox.Provision.Stage.Approved:
            raise exceptions.resource.Unavailable("VM is currently installing/already installed")

        def provision_stage(stage: models.proxmox.Provision.Stage):
            vm.metadata.provision.stage = stage
            vm.metadata.provision.remarks = []
            self.write_out_metadata(vm)

        def provision_remark(line: str):
            vm.metadata.provision.remarks.append(line)
            self.write_out_metadata(vm)

        def provision_failed(reason: str):
            provision_stage(models.proxmox.Provision.Stage.Failed)
            provision_remark(reason)
            raise exceptions.resource.Unavailable(f"VM {vm.hostname} installation failed, check remarks")

        #provision_stage(models.proxmox.Provision.Stage.DownloadImage)

        image_folder = f"/tmp/admin-api/"
        image_path = f"/tmp/admin-api/{vm.metadata.provision.image.disk_sha256sum}"

        # should be unique per API worker
        download_folder = f"/tmp/admin-api-{socket.gethostname()}-{os.getpid()}/"
        download_path = f"/tmp/admin-api-{socket.gethostname()}-{os.getpid()}/{vm.metadata.provision.image.disk_sha256sum}"

        with ProxmoxNodeSSH(vm.node) as con:
            # See if the image exists
            try:
                con.sftp.stat(image_path)

                # Checksum image    
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"sha256sum {image_path} | cut -f 1 -d' '"
                )

                if vm.metadata.provision.image.disk_sha256sum not in str(stdout.read()):
                    provision_failed(f"Downloaded image does not pass SHA256SUMS given {status}: {stderr.read()} {stdout.read()}")

            except Exception as e:
                # Original image does not exist, we gotta download it
                stdin, stdout, stderr = con.ssh.exec_command(
                    f"rm -f {download_path} || mkdir -p {download_folder} && wget {vm.metadata.provision.image.disk_url} -O {download_path}"
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
                    f"mkdir -p {image_folder} && rm -rf {image_path} && mv {download_path} {image_path}"
                )

                status = stdout.channel.recv_exit_status()
                if status != 0:
                    provision_failed(f"Couldn't rename VM image {status}: {stderr.read()} {stdout.read()}")
            
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

            # Set specs
            self.prox.nodes(vm.node).qemu(f"{vm.id}/config").put(**{
                'virtio0': f"{config.proxmox.uservm.dir_pool}:{vm.id}/primary.{ vm.metadata.provision.image.disk_format}",
                'cores': vm.metadata.provision.image.specs.cores,
                'memory': vm.metadata.provision.image.specs.memory,
                'bios': 'ovmf',
                'efidisk0': f"{config.proxmox.uservm.dir_pool}:{vm.id}/efi.qcow2",
                'scsihw': 'virtio-scsi-pci',
                'machine': 'q35',
                'serial0': 'socket',
            })

            self.prox.nodes(vm.node).qemu(f"{vm.id}/resize").put(**{
                'disk': 'virtio0',
                'size': f'{vm.metadata.provision.image.specs.disk_space}G'
            })  
            
    def start_uservm(
        self,
        vm : models.proxmox.UserVM
    ):
        # install cloud-init data
        with ProxmoxNodeSSH(vm.node) as con:
            snippets_path = self.prox.storage(config.proxmox.uservm.dir_pool).get()['path'] + "/snippets"

            con.sftp.put(
                io.StringIO(""),
                f'{ snippets_path }/{vm.fqdn}.metadata.yml'
            )

            con.sftp.put(
                io.StringIO(f"""
                    #cloud-config
                    preserve_hostname: false
                    manage_etc_hosts: true
                    fqdn: { vm.fqdn }
                    packages:
                        - qemu-guest-agent
                    runcmd:
                        - [ systemctl, enable, qemu-guest-agent ]
                        - [ systemctl, start, qemu-guest-agent, --no-block ]  
                    users:
                        -   name: root
                            lock-passwd: false
                            passwd: 
                            ssh_authorized_keys:
                                - "{{ lookup('file', './keys/games/id_rsa.pub') }}"
                    apt: 
                        preserve_sources_list: true
                        primary:
                            - arches: [default]
                                uri: http://ie.archive.ubuntu.com/ubuntu/
                        security:
                        - uri: http://security.ubuntu.com/ubuntu
                """),
                f'{ snippets_path }/{vm.fqdn}.userdata.yml'
            )



        self.prox.nodes(vm.node).qemu(f"{vm.id}/status/start").post()

    def stop_uservm(
        self,
        vm : models.proxmox.UserVM
    ):
        # Stop VM and delete cloudinit stuff
    
        pass
    
    def shutdown_uservm(
        self,
        vm : models.proxmox.UserVM
    ):
        self.prox.nodes(vm.node).qemu(f"{vm.id}/status/shutdown").post()

        with ProxmoxNodeSSH(vm.node) as con:
            pass    
