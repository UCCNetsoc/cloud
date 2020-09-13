
import os
import io
import tarfile
import logging
import mimetypes
import selectors
import subprocess

from typing import List
from pathlib import Path
from v1 import models, exceptions, utilities
from v1.config import config

from fastapi.responses import StreamingResponse

class HomeDirFolder:
    def __init__(self):
        pass

    def _get_account_backups_path(
        self,
        account: models.account.Account
    ) -> Path:
        path = account.home_dir.joinpath(config.backups.folder)

        if not path.exists():
            raise exceptions.resource.NotFound(f"could not get backups path: path {path} does not exist")

        return path


    def _get_account_backup_path(
        self,
        account: models.account.Account,
        name: str
    ) -> Path:
        path = account.home_dir.joinpath(config.backups.folder).joinpath(name)

        if not path.exists():
            raise exceptions.resource.NotFound(f"could not get backup path for backup {name}: path {path} does not exist")

        return path

    def read_by_account(
        self,
        account: models.account.Account,
        name: str
    ) -> models.backup.Backup:
        return models.backup.Backup(
            name=name,
            path=self._get_account_backup_path(account, name),
            uid=account.uid
        )
    
    def list_by_account(
        self,
        account: models.account.Account,
    ) -> List[models.backup.Backup]:
        d = self._get_account_backups_path(account)

        backups = []

        for file in d.iterdir():
            backups.append(self.read_by_account(account, file.name))

        return backups


    def stream_backup(
        self,
        backup: models.backup.Backup
    ) -> bytes:

        base_path = backup.path
        
        if not base_path.exists():
            raise exceptions.resource.NotFound(f"could not find backup {backup.name}: does not exist")
        
        if base_path.is_file():
            with utilities.su.Guard(backup.uid, backup.uid):
                f = open(base_path, mode="rb")

            return StreamingResponse(f,
                media_type=mimetypes.guess_type(base_path)[1],
                headers={
                    "Content-Disposition": f'attachment; filename="{ backup.name }"'
                }
            )
        elif base_path.is_dir():
            def targz_stream():
                def demote(uid, gid):
                    os.setgid(gid)
                    os.setuid(uid)

                tar = subprocess.Popen(["tar", "-cf", "-", base_path.name], stdout=subprocess.PIPE, preexec_fn=demote(backup.uid, backup.uid), cwd=base_path.parent)
                pigz = subprocess.Popen(["pigz", "--best", "-c", "-f"], stdin=tar.stdout, stdout=subprocess.PIPE, preexec_fn=demote(backup.uid, backup.uid), cwd=base_path.parent)

                sel = selectors.DefaultSelector()
                sel.register(pigz.stdout, selectors.EVENT_READ)

                chunk_size = os.cpu_count() * 128000 # Cpu Cores * pigz 128K Blocks
                while True:
                    key, _ = sel.select()[0]
                    data = key.fileobj.read(chunk_size)
                    if not data:
                        return
                    yield data

            return StreamingResponse(
                targz_stream(),
                media_type="application/gzip",
                headers={
                    "Content-Disposition": f'attachment; filename="{ backup.name }.tar.gz"'
                }
            )
        else:
            raise exceptions.resource.NotFound(f"could not find backup {backup.name}: directory is not a folder or does not exist")

    


