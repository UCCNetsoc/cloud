
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