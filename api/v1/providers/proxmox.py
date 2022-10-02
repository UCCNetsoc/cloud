
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
import random
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
    """
        Paramiko SSH client that will first SSH into an exposed Proxmox node, then jump into any of the nodes in the Cluster
        Expects that each cluster node is reachable by just it's short hostname,

        i.e "ssh leela" should ssh into a clusternode named leela

        Contains ssh and sftp objects for use within the manager
    """

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

    def _get_instance_type_base_fqdn(
        self,
        instance_type: models.proxmox.Type
    ):
        """Returns the base fqdn for an instance type, i.e vps.netsoc.cloud"""

        if instance_type == models.proxmox.Type.LXC:
            return f"container.{config.proxmox.network.base_fqdn}"
        elif instance_type == models.proxmox.Type.VPS:
            return f"vps.{config.proxmox.network.base_fqdn}"

    def _get_instance_fqdn_for_username(
        self,
        instance_type: models.proxmox.Type,
        username: str,
        hostname: str
    ) -> str:
        """Returns the base fqdn for an instance owned by a username, i.e ocanty.vps.netsoc.cloud"""

        return f"{hostname}.{username}.{self._get_instance_type_base_fqdn(instance_type)}"

    def _get_instance_fqdn_for_account(
        self,
        instance_type: models.proxmox.Type,
        account: models.account.Account,
        hostname: str
    ) -> str:
        """Returns the base fqdn for an instance owned by an account, i.e ocanty.vps.netsoc.cloud"""

        return self._get_instance_fqdn_for_username(instance_type, account.username, hostname)

    def _allocate_nic(
        self
    ) -> models.proxmox.NICAllocation:
        """Examine all other instances and find a new IP and NIC stuff like mac address"""
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
        for fqdn, instance in self.read_all_instances(ignore_errors=True).items():
            for address in instance.metadata.network.nic_allocation.addresses:
                if address.ip in ips:
                    ips.remove(address.ip)
    
        if len(ips) > 0:
            ip_addr = random.sample(list(ips),1)[0]

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
        """Turns metadata into readable yaml so it looks pretty in the Proxmox web ui"""
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
        """Write metadata to the instances description in Proxmox"""

        yaml_description = self._serialize_metadata(instance.metadata)
        
        if instance.type == models.proxmox.Type.LXC:
            self.prox.nodes(f"{instance.node}/lxc/{instance.id}/config").put(description=yaml_description)
        elif instance.type == models.proxmox.Type.VPS:
            self.prox.nodes(f"{instance.node}/qemu/{instance.id}/config").put(description=yaml_description)

    def _hash_fqdn(
        self,
        fqdn: str
    ) -> int:
        """Hash a fqdn string and return an id to use in Proxmox"""
        random.seed(fqdn)
        hash_id = random.randint(1000, 5000000)
        random.seed()

        return hash_id

    def create_instance(
        self,
        instance_type: models.proxmox.Type,
        account: models.account.Account,
        hostname: str,
        request_detail: models.proxmox.InstanceRequestDetail
    ):
        """Create an instance of type associated with a user account with hostname and requested detail like template"""

        # get template data
        template = self.read_template(instance_type, request_detail.template_id)

        # see if instance with this hostname already exists
        try: 
            existing_vm = self.read_instance_by_account(instance_type, account, hostname)
            raise exceptions.resource.AlreadyExists(f"Instance {hostname} already exists")
        except exceptions.resource.NotFound:
            pass

        # get the base fqdn for this users account username
        fqdn = self._get_instance_fqdn_for_account(instance_type, account, hostname)

        # Give the host it's fqdn by default as a vhost
        # (we allow this in validate_domain)
        password, user_ssh_private_key, root_user = self._generate_instance_root_user()

        fancy_name = "unknown"
        if instance_type == models.proxmox.Type.LXC:
            fancy_name = "container"
        elif instance_type == models.proxmox.Type.VPS:
            fancy_name = "vps"

        vhosts = {}
        vhosts[f"{hostname}-{account.username}-{fancy_name}.{config.proxmox.network.vhosts.service_subdomain.base_domain}"] = models.proxmox.VHostOptions(
            port=80,
            https=False
        )

        # set metadata for the proxmox description
        metadata = models.proxmox.Metadata(
            owner=account.username,
            template_metadata=template.metadata,
            reason=request_detail.reason,
            inactivity=models.proxmox.Inactivity(
                marked_active_at=datetime.date.today()
            ),
            network=models.proxmox.Network(
                nic_allocation=self._allocate_nic(),
                vhosts=vhosts
            ),
            root_user=root_user,
            wake_on_request=template.metadata.wake_on_request
        )

        # get hash for the vm id
        hash_id = self._hash_fqdn(fqdn)

        if instance_type == models.proxmox.Type.LXC:
            metadata.groups = set(["netsoc_cloud_container", "netsoc_cloud_instance"])
        elif instance_type == models.proxmox.Type.VPS:
            metadata.groups = set(["netsoc_cloud_vps", "netsoc_cloud_instance"])

            
        yaml_description = self._serialize_metadata(metadata)

        # pick a node for the instance based off the required specs
        target_node_name = self._select_best_node(template.specs)

        # we need to clone the template to the node its stored on and then migrate it to the target node
        # (this lets us use templates without shared storage)

        if instance_type == models.proxmox.Type.LXC:
            self.prox.nodes(f"{template.node}/lxc/{template.id}/clone").post(**{
                "hostname": fqdn,
                "newid": hash_id,
                "description": yaml_description,
                "storage": config.proxmox.instance_dir_pool,
                "pool": "netsoc_cloud",
                "full": 1
            })

            self._wait_for_instance_created(instance_type, fqdn)
            instance = self._read_instance_by_fqdn(instance_type, fqdn)

            if instance.node != target_node_name:
                self.prox.nodes(f"{instance.node}/lxc/{instance.id}/migrate").post(**{
                    "target": target_node_name,
                    "restart": 1
                })

        elif instance_type == models.proxmox.Type.VPS:
            self.prox.nodes(f"{template.node}/qemu/{template.id}/clone").post(**{
                "name": fqdn,
                "newid": hash_id,
                "description": yaml_description,
                "storage": config.proxmox.instance_dir_pool,
                "pool": "netsoc_cloud",
                "full": 1
            })

            self._wait_for_instance_created(instance_type, fqdn)
            instance = self._read_instance_by_fqdn(instance_type, fqdn)

            if instance.node != target_node_name:
                self.prox.nodes(f"{instance.node}/qemu/{instance.id}/migrate").post(**{
                    "target": target_node_name
                })

        self._wait_for_instance_migrated(instance.type, instance.fqdn, target_node_name)
        

    def delete_instance(
        self,
        instance: models.proxmox.Instance
    ):
        """Delete an instance"""

        if instance.status != models.proxmox.Status.Stopped:
            raise exceptions.resource.Unavailable("Cannot delete instance, instance is running")

        if instance.type == models.proxmox.Type.LXC:
            self.prox.nodes(instance.node).lxc(f"{instance.id}").delete()
        elif instance.type == models.proxmox.Type.VPS:
            # delete cloud-init data
            with ClusterNodeSSH(instance.node) as con:
                snippets_path = self.prox.storage(config.proxmox.instance_dir_pool).get()['path'] + "/snippets"

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
        timeout: int = 300,
        poll_interval: int = 1
    ):
        """Wait for an instance of the specified name to appear in the Proxmox cluster"""

        start = time.time()
        while True:
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

    def _wait_for_instance_migrated(
        self,
        instance_type: models.proxmox.Type,
        fqdn: str,
        target_node: str,
        timeout: int = 300,
        poll_interval: int = 1
    ):
        """Wait for an instance of the specified name to be migrated in the Proxmox cluster"""

        start = time.time()
        while True:
            now = time.time()

            lxcs_qemus = self.prox.cluster.resources.get(type="vm")

            for entry in lxcs_qemus:
                if 'name' in entry and entry['name'] == fqdn and entry['node'] == target_node: 
                    if instance_type == models.proxmox.Type.LXC:
                        config = self.prox.nodes(f"{entry['node']}/lxc/{entry['vmid']}/config").get()

                        if 'lock' not in config and 'hostname' in config and config['hostname'] == fqdn:
                            return

                    elif instance_type == models.proxmox.Type.VPS:
                        config = self.prox.nodes(f"{entry['node']}/qemu/{entry['vmid']}/config").get()

                        if 'name' in config and config['name'] == fqdn and 'lock' not in config:
                            return

            if (now-start) > timeout:
                raise exceptions.resource.Unavailable(f"Timeout occured waiting for instance to be migrated")

            time.sleep(poll_interval)

    def _get_template_base_fqdn(
        self
    ):
        return f"template.{config.proxmox.network.base_fqdn}"

    def _get_template_type_base_fqdn(
        self,
        instance_type: models.proxmox.Type
    ):
        if instance_type == models.proxmox.Type.VPS:
            return f"vps.{self._get_template_base_fqdn()}"
        elif instance_type == models.proxmox.Type.LXC:
            return f"container.{self._get_template_base_fqdn()}"

    def _get_template_fqdn(
        self,
        instance_type: models.proxmox.Type,
        hostname: str,
    ) -> str:
        return f"{hostname}.{self._get_template_type_base_fqdn(instance_type)}"

    def _read_template_on_node(
        self,
        instance_type: models.proxmox.Type,
        node: str,
        vmid: int,
        expected_fqdn: Optional[str] = None
    ) -> models.proxmox.Template:
        """Read instance by reading the vm/container on proxmox and parsing the description metadata"""

        if instance_type == models.proxmox.Type.LXC:
            try:
                lxc_config = self.prox.nodes(f"{node}/lxc/{vmid}/config").get()
            except Exception as e:
                raise exceptions.resource.NotFound("The template does not exist")

            logger.info(lxc_config)
            if not 'template' in lxc_config or lxc_config['template'] != 1:
                raise exceptions.resource.NotFound("The specified VMID is not a template")

            fqdn = lxc_config['hostname']

            if expected_fqdn is not None and fqdn != expected_fqdn:
                raise exceptions.resource.NotFound("The template at the specified VM ID does not have the expected FQDN")

            # decode description
            try:
                metadata = models.proxmox.TemplateMetadata.parse_obj(
                    yaml.safe_load(lxc_config['description'])
                )
            except Exception as e:
                raise exceptions.resource.Unavailable(
                    f"Template is unavailable, malformed metadata description: {e}"
                )


            hostname = fqdn.split(".")[0]

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

            template = models.proxmox.Template(
                type=instance_type,
                id=vmid,
                fqdn=fqdn,
                node=node,
                hostname=hostname,
                metadata=metadata,
                specs=specs
            )

            return template
        elif instance_type == models.proxmox.Type.VPS:
            try:
                vm_config = self.prox.nodes(f"{node}/qemu/{vmid}/config").get()
            except Exception as e:
                raise exceptions.resource.NotFound("The instance does not exist")

            if not 'template' in vm_config or vm_config['template'] != 1:
                raise exceptions.resource.NotFound("The specified VMID is not a template")

            fqdn = vm_config['name']

            if expected_fqdn is not None and fqdn != expected_fqdn:
                raise exceptions.resource.NotFound("The instance at the specified VM ID does not have the expected FQDN")
            
            # decode description
            try:
                metadata = models.proxmox.TemplateMetadata.parse_obj(
                    yaml.safe_load(vm_config['description'])
                )
            except Exception as e:
                raise exceptions.resource.Unavailable(
                    f"Instance is unavailable, malformed metadata description: {e}"
                )

            hostname = fqdn.split(".")[0]

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

            template = models.proxmox.Template(
                type=instance_type,
                id=vmid,
                fqdn=fqdn,
                node=node,
                hostname=hostname,
                metadata=metadata,
                specs=specs
            )

            return template

        raise exceptions.resource.NotFound("The template does not exist")

    def _read_template_by_fqdn(
        self,
        instance_type: models.proxmox.Type,
        fqdn: str
    ) -> models.proxmox.Template:
        lxcs_qemus = self.prox.cluster.resources.get(type="vm") # also gets containers :shrug:

        for entry in lxcs_qemus:
            if 'name' in entry and entry['name'] == fqdn:
                instance = self._read_template_on_node(instance_type, entry['node'], entry['vmid'])
                return instance

        raise exceptions.resource.NotFound("The template does not exist")

    def read_template(
        self,
        instance_type: models.proxmox.Type,
        hostname: str
    ):
        return self._read_template_by_fqdn(instance_type, self._get_template_fqdn(instance_type, hostname))
        
    def read_templates(
        self,
        instance_type: models.proxmox.Type,
        ignore_errors: bool = True
    ) -> Dict[str, models.proxmox.Template]:
        ret = { }

        # query multiple types

        lxcs_qemus = self.prox.cluster.resources.get(type="vm")

        def found_template(typ: models.proxmox.Type, entry: dict):
            try:
                template = self._read_template_on_node(typ, entry['node'], entry['vmid'])
                ret[template.hostname] = template
            except Exception as e:
                if ignore_errors == False:
                    raise e

                logger.info("read_templates ignoring template with error", ignore_errors=ignore_errors, entry=entry, exc_info=True, e=e)

        for entry in lxcs_qemus:
            if instance_type == models.proxmox.Type.VPS:
                if entry['type'] == 'qemu' and 'name' in entry and entry['name'].endswith(self._get_template_type_base_fqdn(models.proxmox.Type.VPS)):
                    found_template(models.proxmox.Type.VPS, entry)

            
            if instance_type == models.proxmox.Type.LXC:
                if entry['type'] == 'lxc' and 'name' in entry and entry['name'].endswith(self._get_template_type_base_fqdn(models.proxmox.Type.LXC)):
                    found_template(models.proxmox.Type.LXC, entry)

        return ret

    # def read_all_templates(
    #     self,
    #     ignore_errors: bool = True:
    # ) -> Dict[str, models.proxmox.Template]:
    #     lxcs = self.read_templates(models.proxmox.Type.LXC)
    #     vpses = self.read_templates(models.proxmox.Type.VPS)

    #     ret = {}
    #     for hostname, instance in lxcs:
    #         ret[instance.fqdn] = instance

    #     for hostname, instance in vpses:
    #         ret[instance.fqdn] = instance

    #     return ret
        

    def _read_instance_on_node(
        self,
        instance_type: models.proxmox.Type,
        node: str,
        vmid: int,
        expected_fqdn: Optional[str] = None
    ) -> models.proxmox.Instance:
        """Read instance by reading the vm/container on proxmox and parsing the description metadata"""

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

            print(current_status.keys())

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
                active=active,
                mem=current_status["mem"],
                disk=current_status["disk"],
                uptime=current_status["uptime"],
            )

            # Build remarks about the vhosts
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
                active=active,
                mem=current_status["mem"],
                disk=current_status["disk"],
                uptime=current_status["uptime"],
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
        lxcs_qemus = self.prox.cluster.resources.get(type="vm") # also gets containers :shrug:

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
                        logger.info("read_instances_by_account ignoring instance with error", instance=entry['name'], ignore_errors=ignore_errors, e=e, exc_info=True)
                else:
                    instance = self._read_instance_on_node(instance_type, entry['node'], entry['vmid'])
                    ret[instance.hostname] = instance
        
                        
        return ret

    def read_instances(
        self,
        instance_type: models.proxmox.Type = None,
        ignore_errors: bool = True
    ) -> Dict[str, models.proxmox.Instance]:
        """Read all instances in the cluster, dict indexed by fqdn, special flag to ignore instances that cause exceptions on reading"""

        # query multiple types
        ret = {}

        lxcs_qemus = self.prox.cluster.resources.get(type="vm")

        def found_instance(typ: models.proxmox.Type, entry: dict):
            try:
                instance = self._read_instance_on_node(typ, entry['node'], entry['vmid'])
                ret[instance.fqdn] = instance

            except Exception as e:
                if ignore_errors == False:
                    raise e

                logger.info("read_instances ignoring template with error", ignore_errors=ignore_errors, entry=entry, exc_info=True, e=e)


        if instance_type == models.proxmox.Type.VPS or instance_type == None:
            for entry in lxcs_qemus:
                if entry['type'] == 'qemu' and 'name' in entry and entry['name'].endswith(self._get_instance_type_base_fqdn(models.proxmox.Type.VPS)):
                    found_instance(models.proxmox.Type.VPS, entry)
        
        
        if instance_type == models.proxmox.Type.LXC or instance_type == None:
            for entry in lxcs_qemus:
                if entry['type'] == 'lxc' and 'name' in entry and entry['name'].endswith(self._get_instance_type_base_fqdn(models.proxmox.Type.LXC)):
                    found_instance(models.proxmox.Type.LXC, entry)

        return ret


    def read_all_instances(
        self,
        ignore_errors: bool = True
    ) -> Dict[str, models.proxmox.Instance]:
        return self.read_instances(ignore_errors=ignore_errors)


    def _generate_instance_root_user(
        self
    ) -> Tuple[str, str, models.proxmox.RootUser]:
        """Returns <password>, <private key>, <public root user info>"""

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
        """Reset a running instances root user returns a tuple of password, private_key"""

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
        """start instance, clear cloudinit flag can clear the cloud-init provisioning data off a vps if required"""

        if instance.type == models.proxmox.Type.LXC:
            # apply network adapter settings in case they changed
            netconf = {
                "rate": "12.5", # 12.5MB/s
                "name": "eth0",
                "bridge": config.proxmox.network.bridge,
                "hwaddr": instance.metadata.network.nic_allocation.macaddress,
                "ip": instance.metadata.network.nic_allocation.addresses[0],
                "gw": instance.metadata.network.nic_allocation.gateway4,
                "mtu": 1500
            }

            if instance.metadata.network.nic_allocation.vlan is not None:
                netconf["tag"] = instance.metadata.network.nic_allocation.vlan 

            self.prox.nodes(instance.node).lxc(f"{instance.id}/config").put(**{
                "nameserver": "1.1.1.1",
                "net0": build_proxmox_config_string(netconf)
            })

            self.prox.nodes(instance.node).lxc(f"{instance.id}/firewall/options").put(**{
                "macfilter": 1,
                "ipfilter": 1
            })


            self.prox.nodes(instance.node).lxc(f"{instance.id}/status/start").post()
        elif instance.type == models.proxmox.Type.VPS:
            # delete cloud-init data (from a previous run)
            with ClusterNodeSSH(instance.node) as con:
                snippets_path = self.prox.storage(config.proxmox.instance_dir_pool).get()['path'] + "/snippets"

                stdin, stdout, stderr = con.ssh.exec_command(
                    f"rm -f '{ snippets_path }/{instance.fqdn}.networkconfig.yml' '{ snippets_path }/{instance.fqdn}.userdata.yml' '{ snippets_path }/{instance.fqdn}.metadata.yml'"
                )

                # Detach existing cloud-init drive (if any)
                self.prox.nodes(instance.node).qemu(f"{instance.id}/config").put(
                    ide2="none,media=cdrom",
                    cicustom=""
                )

                # install cloud-init data
                snippets_path = self.prox.storage(config.proxmox.instance_dir_pool).get()['path'] + "/snippets"


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
        mtu: 1500
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
                    "user": f"{ config.proxmox.instance_dir_pool }:snippets/{instance.fqdn}.userdata.yml",
                    "network": f"{ config.proxmox.instance_dir_pool }:snippets/{instance.fqdn}.networkconfig.yml",
                    "meta": f"{ config.proxmox.instance_dir_pool }:snippets/{instance.fqdn}.metadata.yml"
                }),
                ide2=f"{ config.proxmox.instance_dir_pool }:cloudinit,format=qcow2"
            )

            netconf = {
                "virtio": instance.metadata.network.nic_allocation.macaddress,
                "bridge": config.proxmox.network.bridge,
                "rate": "12.5" # 12.5MBps
            }

            if instance.metadata.network.nic_allocation.vlan is not None:
                netconf["tag"] = instance.metadata.network.nic_allocation.vlan 

            # Set network card
            self.prox.nodes(instance.node).qemu(f"{instance.id}/config").put(
                net0=build_proxmox_config_string(netconf)
            )

            
            # Setup IP/ARP filter to prevent spoofing attacks
            self.prox.nodes(instance.node).qemu(f"{instance.id}/firewall/options").put(**{
                "macfilter": 1,
                "ipfilter": 1
            })

            # add firewall rules for the ip filter, i.e only allow the vps to send out traffic with its own ip
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
        # reset inactivity status
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
        """Add a vhost to an instance, exception if domain is used by another instance"""

        if not self.is_domain_available(vhost):
            raise exceptions.resource.Unavailable(f"This domain/vhost is currently in use by another user or instance.")

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
        self,
        instances: Dict[str, models.proxmox.Instance] = None
    ) -> Dict[int,Tuple[str, ipaddress.IPv4Address, int]]:
        """
        Build a dict indexed by external port number returning a tuple of (fqdn, ip address, internal port number) of the port mappings
        needed by the cluster
        """

        all_instances = None

        if instances == None:
            all_instances = self.read_all_instances(ignore_errors=True)
        else:
            all_instances = instances

        port_map = {}

        for fqdn, instance in all_instances.items():
            
 
            for external_port, internal_port in instance.metadata.network.ports.items():
  
                if external_port in port_map:
                    logger.info(f"warning, conflicting port map: {instance.fqdn} tried to map {external_port} but it's already taken!")
                    continue

                if config.proxmox.network.port_forward.range[0] > external_port or external_port > config.proxmox.network.port_forward.range[1]:
                    logger.info(f"warning, port out of range: {instance.fqdn} tried to map {external_port} but it's out of range!")
                    continue

                port_map[external_port] = (instance.fqdn, instance.metadata.network.nic_allocation.addresses[0].ip, internal_port)
        
        return port_map

    def get_random_available_external_port(
        self,
        instances: Dict[str, models.proxmox.Instance] = None
    ) -> Optional[int]:
        port_map = self.get_port_forward_map(instances)

        occupied_set = set(port_map.keys())
        full_range_set = set(range(config.proxmox.network.port_forward.range[0],config.proxmox.network.port_forward.range[1]+1))

        remaining = full_range_set-occupied_set

        if len(remaining) > 0:
            return random.choice(tuple(remaining))
        
        raise exceptions.resource.Unavailable("out of suitable external ports")

    def is_domain_available(
        self,
        domain: str
    ) -> bool:
        """Returns False if the domain is in use by another instance"""

        for fqdn, instance in self.read_all_instances(ignore_errors=True).items():
            # first do vhosts
            for vhost, options in instance.metadata.network.vhosts.items():
                valid, remarks = self.validate_domain(instance, vhost)

                if valid is True and domain == vhost:
                    return False
                
        return True

    def validate_domain(
        self,
        instance: models.proxmox.Instance,
        domain: str
    ) -> (bool, Optional[List[str]]):
        """
        Verifies a single domain, if the domain is valid, (True, None) is returned
        If the domain is invalid, (False, a list of remarks is returned)
        """
        username = instance.metadata.owner

        txt_name = config.proxmox.network.vhosts.user_domain.verification_txt_name
        txt_content = username

        base_domain = config.proxmox.network.vhosts.service_subdomain.base_domain
        allowed_a_aaaa = config.proxmox.network.vhosts.user_domain.allowed_a_aaaa

        split = domain.split(".")

        remarks = []

        # *.netsoc.cloud etc
        if domain.endswith(f".{base_domain}"):
            # the stuff at the start, i.e if they specified blog.ocanty.netsoc.cloud
            # prefix is blog.ocanty
            # we only allow a single subdomain, so we gotta stop this in its tracks
            prefix = domain[:-len(f".{base_domain}")]
            split_prefix = prefix.split(".")
            
            if len(split_prefix) != 1:
                remarks.append(f"Invalid domain {domain}: only allowed a subdomain up one level, e.g. 'example.{base_domain}'")

            if split_prefix[-1] in config.proxmox.network.vhosts.service_subdomain.blacklisted_subdomains:
                remarks.append(f"Invalid domain {domain}: the subdomain '{ split_prefix[-1] }'' is blacklisted")

        else: # custom domain
            try:
                info_list = socket.getaddrinfo(domain, 80)
            except Exception as e:
                remarks.append(f"Could not verify custom domain: {e}, is the domain registered? (can take a 20-30 mins to update)")
                return (False, remarks)

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
        """
        Return a traefik config that will add rules for doing port mappings and
        vhost reverse proxying
        """
        # Traefik does not like keys with empty values
        # so we gotta omit them by checking if the base key is already in the dict everywhere
        c = {}

        services = {}
        routers = {}

        instances = self.read_all_instances(ignore_errors=True)

        for fqdn, instance in instances.items():
            fqdn_prefix = instance.fqdn.replace('.', '-')

            # first do vhosts
            for vhost, options in instance.metadata.network.vhosts.items():
                valid, remarks = self.validate_domain(instance, vhost)
                
                vhost_suffix = vhost.replace('.', '-')

                if valid is True:
                    if 'http' not in c:
                        c['http'] = {
                            'routers': {},
                            'services': {}
                        }
                    
                    if vhost.endswith(config.proxmox.network.vhosts.service_subdomain.base_domain):
                        c['http']['routers'][f"{fqdn_prefix}-{vhost_suffix}"] = {
                            "entrypoints": web_entrypoints,
                            "rule": f"Host(`{vhost}`)",
                            "service": f"{fqdn_prefix}-{vhost_suffix}",
                            "tls": {
                                "certResolver": f"{ config.proxmox.network.traefik.service_subdomain_cert_resolver }",
                            }
                        }
                    else:
                        c['http']['routers'][f"{fqdn_prefix}-{vhost_suffix}"] = {
                            "entrypoints": web_entrypoints,
                            "rule": f"Host(`{vhost}`)",
                            "service": f"{fqdn_prefix}-{vhost_suffix}",
                            "tls": {
                                "certResolver": f"{ config.proxmox.network.traefik.user_domain_cert_resolver }",
                            }
                        }

                    proto = "http"

                    if options.https is True:
                        proto = "https"

                    c['http']['services'][f"{fqdn_prefix}-{vhost_suffix}"] = {
                        "loadBalancer": {
                            "servers": [{ 
                                "url": f"{ proto }://{instance.metadata.network.nic_allocation.addresses[0].ip}:{ options.port }"
                            }]
                        }
                    }


        # then do tcp/udp port mappings
        for external_port, internal_tuple in self.get_port_forward_map(instances).items():
            fqdn, ip, internal_port = internal_tuple
            fqdn_prefix = fqdn.replace('.', '-')
            
            if 'tcp' not in c and 'udp' not in c:
                c['tcp'] = {
                    'routers': {},
                    'services': {}
                }

                c['udp'] = {
                    'routers': {},
                    'services': {}
                }

            c['tcp']['routers'][f"{fqdn_prefix}-{external_port}-tcp"] = {
                "entryPoints": [f"netsoc-cloud-{external_port}-tcp"],
                "rule": "HostSNI(`*`)",
                "service": f"{fqdn_prefix}-{external_port}-tcp"
            }

            c['tcp']['services'][f"{fqdn_prefix}-{external_port}-tcp"] = {
                "loadBalancer": {
                    "servers": [{
                        "address": f"{ip}:{internal_port}"
                    }]
                }
            }

            c['udp']['routers'] [f"{fqdn_prefix}-{external_port}-udp"] = {
                "entryPoints": [f"netsoc-cloud-{external_port}-udp"],
                "service": f"{fqdn_prefix}-{external_port}-udp"
            }

            c['udp']['services'] [f"{fqdn_prefix}-{external_port}-udp"] = {
                "loadBalancer": {
                    "servers": [{
                        "address": f"{ip}:{internal_port}"
                    }]
                }
            }
            

        return c
