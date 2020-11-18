import os
import io
import tarfile
import logging
import mimetypes
import selectors
import subprocess
import stat
import pathlib
import paramiko
from io import StringIO

import stat as st
from typing import List, Dict
from v1 import models, utilities, exceptions
from v1.utilities import su
from v1.config import config

import structlog as logging

from fastapi import Path, File, UploadFile
from fastapi.responses import StreamingResponse


class FileManager:
    logger = logging.getLogger(f"{__name__}.filemanager")


    def __init__(self):
        pass


    def _is_dir(self, path: str = Path(default="/")) -> bool:
        return path.is_dir()


    def ls(
        self,
        account: models.account.Account,
        fqdn: str,
        path: Path(default="/"),
    ) -> List[paramiko.SFTPAttributes]:
        try:
            privkey = paramiko.RSAKey.from_private_key("")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
            ftp = ssh.connect( fqdn, 22, "root", pkey=privkey ).open_sftp()

        except ConnectionError:
            raise exceptions.rest.Error(403, "couldn't connect to remote server")

        print(
            f"listing directories in { path } for user { account.username }, on { fqdn }"
        )
        resp = ftp.listdir_attr(path)
        ssh.close()
        return resp


    def stat(
        self, account: models.account.Account, fqdn: str, path: str = Path(default="/")
    ) -> str:
        try:
            privkey = paramiko.RSAKey.from_private_key("")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
            ftp = ssh.connect( fqdn, 22, "root", pkey=privkey ).open_sftp()

        except ConnectionError:
            raise exceptions.rest.Error(403, "couldn't connect to remote server")

        print(
            f"listing directories in { path } for user { account.username }, on { fqdn }"
        )
        resp = ftp.stat(path)
        ssh.close()
        return resp


    def chmod(
        self,
        account: models.account.Account,
        fqdn: str,
        mode: int,
        path: str = Path(default="/"),
    ):
        try:
            privkey = paramiko.RSAKey.from_private_key("")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ftp = ssh.connect(fqdn, 22, "root", pkey=privkey).open_sftp()

        except ConnectionError:
            raise exceptions.rest.Error(403, "couldn't connect to remote server")

        print(f"chmod'ing { path }, to { mode } for user { account.username }")

        try:
            resp = ftp.chmod(path, mode)
            ssh.close()
            return resp

        except (FileNotFoundError, FileExistsError):
            raise exceptions.rest.Error(404, "path couldn't be resovled")


    def chown(
        self,
        account: models.account.Account,
        fqdn: str,
        uid: int,
        gid: int,
        path: str = Path(default="/"),
    ):
        try:
            privkey = paramiko.RSAKey.from_private_key("")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ftp = ssh.connect(fqdn, 22, "root", pkey=privkey).open_sftp()

        except ConnectionError:
            raise exceptions.rest.Error(403, "couldn't connect to remote server")

        print(f"chowning'ing { path } for user { account.username }")

        try:
            resp = ftp.chown(path, uid, gid)
            ssh.close()
            return resp

        except FileNotFoundError:
            raise exceptions.rest.Error(404, "path couldn't be resovled")

        except PermissionError:
            raise exceptions.rest.Error(403, "permission denied for provided path")


    def touch(
        self,
        account: models.account.Account,
        fqdn: str,
        path: str = Path(default="/"),
    ):
        try:
            privkey = paramiko.RSAKey.from_private_key("")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ftp = ssh.connect(fqdn, 22, "root", pkey=privkey).open_sftp()

        except ConnectionError:
            raise exceptions.rest.Error(403, "couldn't connect to remote server")

        print(f"touching { path } for user { account.username }")

        try:
            with ftp.open(path, "w+") as file:
                file.write("")
        except IsADirectoryError:
            raise exceptions.rest.Error(409, "given path is a directory")


    def move(
        self,
        account: models.account.Account,
        fqdn: str,
        path: str = Path(default="/"),
        newpath: str = Path(default="/"),
    ):
        try:
            privkey = paramiko.RSAKey.from_private_key("")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ftp = ssh.connect(fqdn, 22, "root", pkey=privkey).open_sftp()

        except ConnectionError:
            raise exceptions.rest.Error(403, "couldn't connect to remote server")

        print(f"mv { path } to { newpath } for user { account.username }")
        ftp.rename(path, newpath)
        ssh.close()


    def mkdir(
        self,
        account: models.account.Account,
        fqdn: str,
        path: str = Path(default="/"),
    ):
        try:
            privkey = paramiko.RSAKey.from_private_key("")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ftp = ssh.connect(fqdn, 22, "root", pkey=privkey).open_sftp()

        except ConnectionError:
            raise exceptions.rest.Error(403, "couldn't connect to remote server")

        print(f"mkdir { path } for user { account.username } on { fqdn }")

        try:
            ftp.mkdir(path)
        except (FileExistsError):
            raise exceptions.rest.Error(409, "path already exists")
        ssh.close()


    def upload_files(
        self,
        account: models.account.Account,
        fqdn: str,
        files: List[UploadFile] = File(...),
        path: str = Path(default="/"),
    ):
        try:
            privkey = paramiko.RSAKey.from_private_key("")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ftp = ssh.connect(fqdn, 22, "root", pkey=privkey).open_sftp()

        except ConnectionError:
            raise exceptions.rest.Error(403, "couldn't connect to remote server")

        print(f"uploading files to { path } for user { account.username } on { fqdn }")

        try:
            for file in files:
                with ftp.open(f"{ path }/{ file.filename }", "wb") as buffer:
                    buffer.write(file.file.read())

        except FileExistsError:
            raise exceptions.rest.Error(409, "file already exists")

        except (FileNotFoundError, NotADirectoryError):
            raise exceptions.rest.Error(409, "couldn't write to given directory")
        ssh.close()

    def get_download(
        self,
        account: models.account.Account,
        path: Path,
    ) -> models.download.Download:
        return models.download.Download(
            path=path,
            name=path.split("/")[-1],
            uid=account.uid,
        )

    def stream_download(
        self,
        download: models.download.Download,
        fqdn: str,
    ) -> bytes:
        try:
            privkey = paramiko.RSAKey.from_private_key("")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ftp = ssh.connect(fqdn, 22, "root", pkey=privkey).open_sftp()

        except ConnectionError:
            raise exceptions.rest.Error(403, "couldn't connect to remote server")

        base_path = download.obj.path

        if not stat.S_ISDIR(ftp.stat(base_path).st_mode):
            try:
                f = ftp.open(base_path, mode="rb")
            except PermissionError:
                raise exceptions.resource.Unavailable(
                    f"Read access denied on { download.obj.path }"
                )

            return StreamingResponse(
                f,
                media_type=mimetypes.guess_type(base_path)[1],
                headers={"Content-Type": "text"},
            )
        else:

            def targz_stream():

                tar_path = ssh.exec_command("whereis tar")
                (_, tarout, _) = ssh.exec_command(f"{tar_path} -cv {base_path}")

                # tar = subprocess.Popen(["tar", "-cf", "-", base_path], stdout=subprocess.PIPE,cwd=pathlib.Path(base_path).parent)
                pigz = subprocess.Popen(
                    ["pigz", "--best", "-c", "-f"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    cwd=pathlib.Path(base_path).parent,
                )

                pigz.stdin.write(tarout.read())
                sel = selectors.DefaultSelector()
                sel.register(pigz.stdout, selectors.EVENT_READ)

                chunk_size = os.cpu_count() * 128000  # Cpu Cores * pigz 128K Blocks
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
                    "Content-Disposition": f"attachment; filename={ download.obj.name }.tar.gz"
                },
            )
        # else:
        #     raise exceptions.resource.NotFound(f"could not find download { str(base_path).split('/')[-1] }: directory is not a folder or does not exist")
