
import os
import io
import tarfile
import logging
import mimetypes

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
                class FileObjStream(object):
                    def __init__(self):
                        self.buffer = io.BytesIO()
                        self.offset = 0

                    def write(self, s):
                        self.buffer.write(s)
                        self.offset += len(s)

                    def tell(self): 
                        return self.offset

                    def close(self):
                        self.buffer.close()

                    def pop(self):
                        s = self.buffer.getvalue()
                        self.buffer.close()

                        self.buffer = io.BytesIO()

                        return s
                
                stream = FileObjStream()

                with tarfile.open(mode="w|gz", fileobj=stream) as tar:
                    for root, dirs, files in os.walk(base_path, topdown=False):
                        for rel_path in files:
                            logging.getLogger("api").info(rel_path)
                            abs_path = base_path.joinpath(rel_path)
                            tar_info = tar.gettarinfo(abs_path, arcname=rel_path)
                            tar.addfile(tar_info)  

                            with open(abs_path, "rb") as file:
                                logging.getLogger("api").info(f"file size: { tar_info.size }")

                                blocks, remainder = divmod(tar_info.size, tarfile.BLOCKSIZE)

                                for b in range(blocks):
                                    block = file.read(tarfile.BLOCKSIZE)

                                    if len(block) < tarfile.BLOCKSIZE:
                                        raise exceptions.resource.Unavailable("unexpected end of data")
                                    
                                    tar.fileobj.write(block)
                                    yield stream.pop()

                                if remainder > 0:
                                    block = file.read(remainder)
                                    tar.fileobj.write(block)
                                    tar.fileobj.write(tarfile.NUL * (tarfile.BLOCKSIZE - remainder))
                                    yield stream.pop()

                                    blocks += 1

                                tar.offset += blocks * tarfile.BLOCKSIZE
                yield stream.pop()

            return StreamingResponse(
                targz_stream(),
                media_type="application/gzip",
                headers={
                    "Content-Disposition": f'attachment; filename="{ backup.name }.tar.gz"'
                }
            )
        else:
            raise exceptions.resource.NotFound(f"could not find backup {backup.name}: directory is not a folder or does not exist")

    


