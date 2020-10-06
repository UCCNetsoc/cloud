
import os
import io
import tarfile
import logging
import mimetypes
import selectors
import subprocess
import pathlib

import stat as st
from typing import List, Dict
from v1 import models, utilities, exceptions
from v1.utilities import su
from v1.config import config

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
        path: Path(default="/"),
    ) -> Dict[str, models.filemanager.Stat]:
        with su.Guard(account.uid, account.uid):

            base_path = path

            try:
                dirs = os.listdir(path)
                stats = {}

                for directory in dirs:
                    path = base_path + '/' + directory
                    statinfo = os.stat(path)

                    stats[str(path).split("/")[-1]] = models.filemanager.Stat(
                            isdir=st.S_ISDIR(statinfo.st_mode),
                            size=statinfo.st_size,
                            uid=statinfo.st_uid,
                            gid=statinfo.st_gid,
                            last_edited=statinfo.st_mtime,
                            perms=str(oct(statinfo.st_mode)[4:])
                    )
                return stats
            except PermissionError:
                raise exceptions.resource.Unavailable(f"Path { path } is not accessible by { account.username }")

            except FileNotFoundError:
                raise exceptions.resource.Unavailable(f"Path { path } was not found")
            except Exception as e:
                raise exceptions.resource.Unavailable(f"REEEEEEEEEEEEE { e }")
    def stat(
        self,
        account: models.account.Account,
        path: str=Path(default="/")
    ) -> os.stat_result:
        with su.Guard(account.uid, account.uid):     
            try:
                statinfo = os.stat(pathlib.Path(path))

                return models.filemanager.Stat(
                    perms=str(oct(statinfo.st_mode)[4:]),
                    # isdir=st.S_ISDIR(statinfo.st_mode),
                    size=statinfo.st_size,
                    uid=statinfo.st_uid,
                    gid=statinfo.st_gid,
                    edited=statinfo.st_mtime,
                )
            except (PermissionError, FileNotFoundError):
                raise exceptions.resource.NotFound(f"Path { path } not accessible")

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

    def stream_download(
        self,
        download: models.download.Download,
    ) -> bytes:
        base_path = download.obj.path

        if not pathlib.Path(base_path).exists():
            raise exceptions.resource.NotFound(f"could not find directory { download.obj.path }: does not exist")

        if pathlib.Path(base_path).is_file():
            with utilities.su.Guard(download.obj.uid, download.obj.uid):
                try:
                    f = open(base_path, mode="rb")
                except PermissionError:
                    raise exceptions.resource.Unavailable(f"Read access denied on { download.obj.path }")

            return StreamingResponse(f,
                media_type=mimetypes.guess_type(base_path)[1],
                headers={
                    "Content-Type": "text"
                }
            )
        elif pathlib.Path(base_path).is_dir():
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
                    "Content-Disposition": f'attachment; filename={ download.obj.name }.tar.gz'
                }
            )
        else:
            raise exceptions.resource.NotFound(f"could not find download { str(base_path).split('/')[-1] }: directory is not a folder or does not exist")
