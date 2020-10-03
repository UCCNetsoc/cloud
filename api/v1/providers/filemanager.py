
import os
import io
import tarfile
import logging
import mimetypes
import selectors
import subprocess

from pydantic import List
from v1 import models, utilities, exceptions
from v1.config import config
from pathlib import Path

import structlog as logging

from fastapi.responses import StreamingResponse

class LSDir():
    logger = logging.getLogger(f"{__name__}.lsdir")
    def __init__(self):
        pass
    
    def ls(
        self,
        account: models.account.Account,
        path: str) -> List(str):
        if not account.home_dir.exists():
            raise exceptions.resource.Unavailable(f"Home directory does not exist for {account.username}")
        else:
            return os.listdir(account.home_dir.joinpath(path))

class Download():
    logger = logging.getLogger(f"{__name__}.download")
    def __init__(self):
        pass

    def _get_download_path(
        self,
        account: models.account.Account,
        path: str
    ) -> Path:
        path = account.home_dir.joinpath(path)

        if not path.exists():
            raise exceptions.resource.NotFound(f"could not get path: path {path} does not exist")

    def get_download(
        self,
        account: models.account.Account,
        path: str
    ) -> models.filemanager.Download:
        return models.filemanager.Download(self._get_download_path(account, path), account.uid)

    def stream_file(
        self,
        download: models.filemanager.Download
    ) -> bytes:
        base_path = download.path

        if not base_path.exists():
            raise exceptions.resource.NotFound(f"could not find directory { download.path }: does not exist")

        if base_path.is_file():
            with utilities.su.Guard(download.uid, download.uid):
                f = open(base_path, mode="rb")

            return StreamingResponse(f,
                media_type=mimetypes.guess_type(base_path)[1],
                headers={
                    "Content-Disposition": f"attachment; filename='{ download.path.split('/')[-1] }'"
                }
            )
        elif base_path.is_dir():
            def targz_stream():
                def demote(uid, gid):
                    os.setgid(gid)
                    os.setuid(uid)

                tar = subprocess.Popen(["tar", "-cf", "-", base_path.name], stdout=subprocess.PIPE, preexec_fn=demote(download.uid, download.uid), cwd=base_path.parent)
                pigz = subprocess.Popen(["pigz", "--best", "-c", "-f"], stdin=tar.stdout, stdout=subprocess.PIPE, preexec_fn=demote(download.uid, download.uid), cwd=base_path.parent)

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
                    "Content-Disposition": f"attachment; filename='{ base_path.split('/')[-1] }.tar.gz'"
                }
            )
        else:
            raise exceptions.resource.NotFound(f"could not find backup { base_path.split('/')[-1] }: directory is not a folder or does not exist")
