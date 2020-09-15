import os
import errno
from pathlib import Path
from typing import Tuple, Dict

import logging
import stat
import yaml
import tarfile
import requests
import socket
import dns
import dns.resolver
import dns.exception
import re
import shutil

from pydantic import EmailStr
from typing import List
from v1 import models, exceptions

from v1.utilities import su
from v1.config import config

class HomeDirFolder():
    """
        Website storage backed by home directories
    """
    def __init__(
        self
    ):
        pass

    def _get_account_websites_path(self, account: models.account.Account):
        path = account.home_dir.joinpath(config.websites.folder)
                
        try:
            path.stat()
        except FileNotFoundError as e:
            raise exceptions.resource.NotFound(f"websites root {path} for {account.username} does not exist")

        return path

    def _get_account_website_path(self, account: models.account.Account, name: models.website.Name, check_exist=True) -> Path:
        path = self._get_account_websites_path(account).joinpath(name)
        
        if check_exist == True:
            try:
                path.stat()
            except FileNotFoundError as e:
                raise exceptions.resource.NotFound(f"website {name} root {path} for {account.username} does not exist")

        return path

    def _get_website_config_path(self, website: models.website.Website) -> Path:
        return website.root.joinpath(config.websites.config_filename)

    def read_in_website_config(
        self,
        website: models.website.Website
    ):
        with su.Guard(website.uid, website.uid):
            config_path = self._get_website_config_path(website)

            try:
                # parse as json
                website.config = models.website.Config.parse_raw(config_path.read_text())
                config_path.chmod(0o400)
            except FileNotFoundError as e:
                # Create the config if it didn't exist
                # print("recreating config")
                self.write_out_website_config(website)

                # raise exceptions.resource.NotFound(f"config file for website {website.name} owned by {website.username} not found")

    def write_out_website_config(
        self,
        website: models.website.Website
    ):
        with su.Guard(website.uid, website.uid):
            config_path = self._get_website_config_path(website)

            try:
                config_path.stat()
            except FileNotFoundError as e:
                config_path.touch()

            config_path.chmod(0o600)
            config_path.write_text(website.config.json())
            config_path.chmod(0o400)

    def create_website(
        self,
        account: models.account.Account,
        name: models.website.Name
    ) -> models.website.Website:    

        with su.Guard(account.uid, account.uid):
            root = self._get_account_website_path(account, name, check_exist=False)

            try:
                os.mkdir(root, 0o755)
            except PermissionError as e:
                raise exceptions.resource.Unavailable(f"unable to write to {account.username}'s home directory")
            except FileExistsError as e:
                raise exceptions.resource.AlreadyExists()
            except FileNotFoundError as e:
                raise exceptions.resource.NotFound(f"unknown user {account.username}")

            website = models.website.Website(
                name=name,
                root=root,
                username=account.username,
                valid=False,
                remarks=[],
                software=models.website.Software.NotInstalled,
                config=models.website.Config(
                    runtime=models.website.Runtime.PHP,
                    hosts=set()
                ),
                uid=account.uid
            )

            # create and write config
            self.write_out_website_config(website)

            return website
    
    def delete_website(
        self, website: models.website.Website
    ):
        with su.Guard(website.uid, website.uid):
            self.uninstall_software(website)
            shutil.rmtree(website.root)
     
    def validate_website(
        self,
        website: models.website.Website
    ):
        # Support <username>.netsoc.co or custom domain name that points to atleast one of 
        # the required A or AAAA records
        # custom domains must have _netsoc.<rest of domain> set to their username
        # so for example
        # I want to setup blog.ocanty.com
        # I must set TXT _netsoc.ocanty.com to "ocanty"
        txt_name = config.websites.dns.txt_name
        txt_content = website.username
        base_domain = config.websites.dns.base_domain
        allowed_a_aaaa = config.websites.dns.allowed_a_aaaa

        remarks = []

        if len(website.config.hosts) == 0:
            remarks.append("No hosts set")
            
        for host in website.config.hosts:
            split = host.split(".")

            # *.netsoc.co
            if host.endswith(f".{base_domain}"):
                subdomain = host[:-len(f".{base_domain}")]
                
                # ensure they use <username>.netsoc.co
                if subdomain != website.username:
                    remarks.append(f"Host {host} - subdomain {subdomain} must be the same as the website owners username {website.username}")

            else: # custom domain
                try:
                    info_list = socket.getaddrinfo(host, 80)
                except Exception as e:
                    remarks.append("Could not verify custom domain: {e}")
                a_aaaa = set(map(lambda info: info[4][0], filter(lambda x: x[0] in [socket.AddressFamily.AF_INET, socket.AddressFamily.AF_INET6], info_list)))
                
                if len(a_aaaa) == 0:
                    remarks.append(f"Host {host} - no A or AAAA records present")

                for record in a_aaaa:
                    if record not in allowed_a_aaaa:
                        remarks.append(f"Host {host} - unknown A/AAAA record on host ({record}), must be one of {allowed_a_aaaa}")

                # we need to check if they have the appropiate TXT record with the correct value
                custom_base = f"{split[len(split)-2]}.{split[len(split)-1]}"

                # check for _netsoc.theirdomain.com 
                try:
                    q = dns.resolver.resolve(f"{txt_name}.{custom_base}", 'TXT')

                    # dnspython returns the TXT record value enclosed in quotation marks
                    # we will need to remove these
                    txt_res = set(map(lambda x: str(x).strip('"'),q))

                    if txt_content not in txt_res:
                        remarks.append(f"Host {host} - could not find TXT record {txt_name} ({txt_name}.{custom_base}) set to {txt_content}, instead found {txt_res}!")

                except dns.resolver.NXDOMAIN:
                    remarks.append(f"Host {host} - could not find TXT record {txt_name} ({txt_name}.{custom_base}) set to {txt_content}")
                except dns.exception.DNSException as e:
                    remarks.append(f"Host {host} - unable to lookup record ({txt_name}.{custom_base}): ({e})")
                except Exception as e:
                    remarks.append(f"Host {host} - error {e} (contact SysAdmins)")

        website.remarks = remarks

        self._detect_software(website)
        website.valid = len(website.remarks) == 0

    class _SoftwareManager:
        def detect(self, website: models.website.Website) -> bool:
            pass

        def install(self, website: models.website.Website, args: models.website.SoftwareArgs):
            
            pass

        def uninstall(self, website: models.website.Website):
            pass
    
    class _WordpressSoftwareManager:
        _wordpress_tgz: bytes = None

        def __init__(self):
            # try:
            #     logging.info("requesting")
            #     r = requests.get("https://wordpress.org/wordpress-5.5.tar.gz", allow_redirects=True)
            #     if r.status_code == 200:
            #         self._wordpress_tgz = r.content
            #     else:
            #         raise exceptions.provider.Unavailable(f"can't get wordpress blob: {r.status_code}")
            # except Exception as e:
            #     logging.info(e)
            #     raise exceptions.provider.Unavailable(f"can't get wordpress blob: {e}")
            try:
                #logging.info("Loading Wordpress tar.gz from /app/v1/assets/wordpress-5.5.tar.gz")
                self._wordpress_tgz = Path("/app/v1/assets/wordpress-5.5.tar.gz").read_bytes()
            except Exception as e:
                raise exceptions.resource.Unavailable(f"Couldn't load Wordpress tar.gz: {e}")

        def detect(self, website: models.website.Website) -> bool:
            return website.root.joinpath("wp-content").exists()

        def install(self, website: models.website.Website, args: models.website.WordpressSoftwareArgs):
            # force validate software args
            args = models.website.WordpressSoftwareArgs.parse_obj(args)

            tar_path = website.root.joinpath("wordpress.tar.gz")
            tar_path.open("w+b").write(self._wordpress_tgz)
            
            with tarfile.open(str(tar_path), "r:gz") as tf:
                logging.info(tf.getnames())
                
                for member in tf.getmembers():
                    if member.name.startswith("wordpress/"):
                        logging.info(member.name)
                        f = tf.extractfile(member)

                        if f is not None:
                            # remove the wordpress/ from the start of the directory and append the website root
                            path = website.root.joinpath(member.name.replace("wordpress/", ""))

                            # mkdir -p the intermediary dirs and write the file
                            os.makedirs(path.parent, mode=0o755, exist_ok=True)
                            with open(path, "wb") as of:
                                of.write(f.read())

                            f.close()
            
            website.root.joinpath("wordpress.tar.gz").unlink()

        def uninstall(self, website: models.website.Website):
            for root, dirs, files in os.walk(str(website.root), topdown=False):
                for name in files:
                    # Delete all files except config file
                    if root != website.root and name != config.websites.config_filename:
                        os.unlink(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))

    class _PHPInfoSoftwareManager:
        _script = "<?php phpinfo(); ?>"

        def install(self, website: models.website.Website, args: models.website.SoftwareArgs):
            website.root.joinpath("index.php").touch()
            website.root.joinpath("index.php").write_text(self._script)

        def uninstall(self, website: models.website.Website):
            website.root.joinpath("index.php").unlink()

        def detect(self, website: models.website.Website):
            return website.root.joinpath("index.php").exists() and website.root.joinpath("index.php").read_text() == self._script
    
    _software_managers = {}
    _software_managers[models.website.Software.Wordpress] = _WordpressSoftwareManager()
    _software_managers[models.website.Software.PHPInfo] = _PHPInfoSoftwareManager()

    def _detect_software(
        self,
        website: models.website.Website
    ):
        with su.Guard(website.uid, website.uid):
            # If only the config file exists in their web root
            if len(list(website.root.iterdir())) == 1 and self._get_website_config_path(website).exists():
                website.software = models.website.Software.NotInstalled
                return

            # Check each software detector
            for software, mgr in self._software_managers.items():
                if mgr.detect(website):
                    website.software = software
                    return

            # If we don't detect the software, it must be the users own software/custom content
            website.software = models.website.Software.Custom

    def install_software(
        self,
        website: models.website.Website,
        software: models.website.Software,
        args: models.website.SoftwareArgs
    ):
        with su.Guard(website.uid, website.uid):
            if software in self._software_managers:
                    if self._detect_software(website):
                        raise exceptions.resource.AlreadyExists(f"the specified software '{software}' is already installed")

                    self._software_managers[software].install(website, args)
            else:
                raise exceptions.resource.NotFound(f"the specified software '{software}' does not have an installer")

    def uninstall_software(
        self,
        website: models.website.Website
    ):
        with su.Guard(website.uid, website.uid):
            if website.software in [models.website.Software.NotInstalled, models.website.Software.Custom, models.website.Software.Unknown]:
                return

            if website.software in self._software_managers:
                self._software_managers[website.software].uninstall(website)
            else:
                raise exceptions.resource.NotFound(f"the specified software '{website.software}' does not have an uninstaller")

    def read_by_account(
        self,
        account: models.account.Account,
        name: models.website.Name
    ) -> models.website.Website:

        with su.Guard(account.uid, account.uid):
            root = self._get_account_website_path(account, name)
            if root.exists():
                if root.is_dir():
                    website = models.website.Website(
                        name=name,
                        root=root,
                        username=account.username,
                        valid=False,
                        remarks=[],
                        software=models.website.Software.Unknown,
                        config=models.website.Config(),
                        uid=account.uid
                    )

                    self.read_in_website_config(website)
                    self.validate_website(website)

                    return website
                else:
                    raise exceptions.resource.NotFound(f"website {name} root {root} is a file, not a folder")
            else:
                raise exceptions.resource.NotFound(f"website {name} root {root} does not exist")
            

    def read_all_by_account(
        self,
        account: models.account.Account
    ) -> Dict[str, models.website.Website]:
        websites = { }

        websites_root = self._get_account_websites_path(account)
        for file in websites_root.iterdir():
            if file.is_dir():
                try:
                    websites[file.stem] = self.read_by_account(account, file.stem)
                except Exception as e:
                    # we need to do this because the name of their webste could be illegal
                    transformed_stem = re.sub(models.website.Name['regex'], "-", file.stem)

                    websites[transformed_stem] = models.website.Website(
                        name=transformed_stem,
                        root=websites_root.joinpath(file.stem),
                        username=account.username,
                        valid=False,
                        remarks=[
                            f"Error: {e} occured when trying to read website"
                        ],
                        software=models.website.Software.Unknown,
                        config=models.website.Config()
                    )
 

        return websites