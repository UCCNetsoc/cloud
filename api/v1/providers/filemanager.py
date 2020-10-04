
import os
import io
import tarfile
import logging
import mimetypes
import selectors
import subprocess
import pathlib

import stat as st
from typing import List
from v1 import models, utilities, exceptions
from v1.config import config
from pathlib import Path

import structlog as logging

from fastapi import Path
from fastapi.responses import StreamingResponse

class FileManager:
    logger = logging.getLogger(f"{__name__}.filemanager")

    def __init__(self):
        pass

    def _is_dir(
        self,
        path: str=Path(default="/")
    ) -> bool:
        return path.is_dir()

    def ls(
        self,
        account: models.account.Account,
        path
    ) -> List[str]:


        if account.home_dir.exists(): base_path = account.home_dir
        else:
            raise exceptions.resouce.Unavailable(f"Home directory does not exist")


        path = base_path.joinpath(path)
        # if not account.home_dir.exists():
        #     raise exceptions.resouce.Unavailable(f"Home directory does not exist for { account.username }")
        # if path.exists() and self._is_dir(path):
        #     return os.listdir(path)
        # else:
        #     raise exceptions.resouceUnavailable(f"Path '{ path }' is not a directory")

        try:
            return os.listdir(path)
        except:
            raise exceptions.resource.Unavailable(f"Path '{ path }' is not a directory or does not exist")

    def stat(
        self,
        account: models.account.Account,
        path: str=Path(default="/")
    ) -> os.stat_result:

        if not pathlib.Path(path).exists():
            raise exceptions.resource.NotFound(f"Path '{path}' does not exist")
        
        statinfo = os.stat(path)

        return models.filemanager.Stat(
            perms=str(oct(statinfo.st_mode)[4:]),
            isdir=st.S_ISDIR(statinfo.st_mode),
            size=statinfo.st_size,
            uid=statinfo.st_uid,
            gid=statinfo.st_gid,
            edited=statinfo.st_mtime,
        )

    def get_download(
        self,
        account: models.account.Account,
        path: Path
    ) -> models.download.Download:

        return models.download.Download(
            path = path,
            name = path.split("/")[-1],
            uid = account.uid,
        )

    def stream_file(
        self,
        download: models.download.Download
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
