
import structlog as logging
import io
import os
import paramiko
import shutil

from v1 import models, utilities, exceptions
from v1.config import config
from pathlib import Path

class MkDir():
    logger = logging.getLogger(f"{__name__}.mkdir")

    def __init__(self):
        pass

    def create(self, account: models.account.Account):
        if account.home_dir.exists():
            raise exceptions.resource.AlreadyExists()

        try:
            shutil.copytree("/etc/skel", account.home_dir)
            os.chown(account.home_dir, account.uid, account.uid)
            for root, dirs, files in os.walk(account.home_dir):
                for d in dirs:
                    os.chown(os.path.join(root,d), account.uid, account.uid)

                for f in files:
                    os.chown(os.path.join(root,f), account.uid, account.uid)

            with utilities.su.Guard(account.uid, account.uid):
                Path(account.home_dir).joinpath(config.websites.folder).mkdir(mode=0o771)


        except Exception as e:
            raise exceptions.provider.Failed(f"could not create home directory: {e}")

# class SSHZFSDataset():
#     _key: paramiko.RSAKey
#     logger = logging.getLogger("v1.providers.mkhomedir.sshzfsdataset")

#     def __init__(self):
#         self._key = paramiko.RSAKey.from_private_key(io.StringIO(config.mkhomedir.sshzfsdataset.ssh_private_key))

#     def create(self, account: models.account.Account):
#         path = Path(account.home_dir)

#         if path.exists():
#             raise exceptions.resource.AlreadyExists()

#         ssh = paramiko.SSHClient()
#         ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#         ssh.connect(
#             config.mkhomedir.sshzfsdataset.ssh_server,
#             config.mkhomedir.sshzfsdataset.ssh_port,
#             config.mkhomedir.sshzfsdataset.ssh_username,
#             config.mkhomedir.sshzfsdataset.ssh_server,
#         )

#         stdin, stdout, stderr = ssh.exec_command(f"sudo zfs create {config.mkhomedir.sshzfsdataset.zpool}{account.home_dir}")
#         out = stdout.readlines()
#         err = stderr.readlines()

#         try:
#             shutil.copy2("/etc/skel", account.home_dir)

#             os.chown(account.home_dir, account.uid, account.uid)
#             for root, dirs, files in os.walk(account.home_dir):
#                 for d in dirs:
#                     os.chown(os.path.join(root,d), account.uid, account.uid)

#                 for f in files:
#                     os.chown(os.path.join(root,f), account.uid, account.uid)

#             with uilities.su.Guard(account.uid, account.uid):
#                 Path(account.home_dir).joinpath(config.websites.folder).mkdir(mode=0o771)

#         except Exception as e:
#             raise exceptions.provider.Failed(f"could not create home directory: {e}")
        