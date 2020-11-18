from fastapi import APIRouter, Depends, Response, File, UploadFile
from fastapi.responses import StreamingResponse

import time
import os
import paramiko
from pathlib import Path
from typing import List, Optional, Dict
from v1 import providers, models, utilities, exceptions
from v1.config import config

import structlog as logging

logger = logging.getLogger(__name__)
logger.info(f"", providers=providers)
router = APIRouter()


@router.get(
    "/{email_or_username}/{instance_type}/{hostname}/ls/{path:path}",
    status_code=200,
)
def list_directory_contents(
    email_or_username: str,
    path: Optional[str],
    hostname: str,
    instance_type: str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account),
):
    fqdn = f"{hostname}.{bearer_account.username}.{instance_type}.cloud.netsoc.co"

    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    if path == None or path == "":
        path = "/"

    return providers.filemanager.ls(account=resource_account, fqdn=fqdn, path=path)


@router.get(
    "/{email_or_username}/{instance_type}/{hostname}/stat/{path:path}",
    status_code=200,
)
def stat_path(
    email_or_username: str,
    instance_type: str,
    hostname: str,
    path: str = Path(default="/"),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account),
):
    fqdn = f"{hostname}.{bearer_account.username}.{instance_type}.cloud.netsoc.co"

    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    return providers.filemanager.stat(account=resource_account, path=path, fqdn=fqdn)


@router.get(
    "/{email_or_username}/{instance_type}/{hostname}/chmod/{mode}/{path:path}",
    status_code=200,
)
def chmod_path(
    email_or_username: str,
    instance_type: str,
    hostname: str,
    mode: int,
    path: str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account),
):
    fqdn = f"{hostname}.{bearer_account.username}.{instance_type}.cloud.netsoc.co"

    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    providers.filemanager.chmod(resource_account, fqdn, mode, path)

    return providers.filemanager.stat(account=resource_account, fqdn=fqdn, path=path)


@router.post(
    "/{email_or_username}/{instance_type}/{hostname}/touch/{path:path}",
    status_code=200,
)
def touch(
    email_or_username: str,
    instance_type: str,
    hostname: str,
    path: str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account),
):
    fqdn = f"{hostname}.{bearer_account.username}.{instance_type}.cloud.netsoc.co"

    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    providers.filemanager.touch(account=resource_account, fqdn=fqdn, path=path)

    return providers.filemanager.stat(resource_account, hostname, path)


@router.post(
    "/{email_or_username}/{instance_type}/{hostname}/mkdir/{path:path}",
    status_code=200,
)
def mkdir(
    email_or_username: str,
    instance_type: str,
    hostname: str,
    path: str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account),
):
    fqdn = f"{hostname}.{bearer_account.username}.{instance_type}.cloud.netsoc.co"

    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    providers.filemanager.mkdir(account=resource_account, fqdn=fqdn, path=path)

    return providers.filemanager.stat(
        account=resource_account, fqdn=hostname, path=path
    )


# move resource
@router.put(
    "/{email_or_username}/{instance_type}/{hostname}/{path:path}",
    status_code=200,
)
def move(
    dest: models.filemanager.Dest,
    email_or_username: str,
    instance_type: str,
    hostname: str,
    path: str = Path(default="/"),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account),
):
    fqdn = f"{hostname}.{bearer_account.username}.{instance_type}.cloud.netsoc.co"

    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    providers.filemanager.move(
        account=resource_account, fqdn=fqdn, path=path, newpath=dest.path
    )

    return providers.filemanager.stat(
        account=resource_account, fqdn=fqdn, newpath=dest.path
    )


# Upload files
@router.post(
    "/{email_or_username}/{instance_type}/{fqdn}/{path:path}",
    status_code=201,
)
def file_upload(
    email_or_username: str,
    instance_type: str,
    hostname: str,
    path: str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account),
    files: List[UploadFile] = File(...),
):
    fqdn = f"{hostname}.{bearer_account.username}.{instance_type}.cloud.netsoc.co"

    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    providers.filemanager.upload_files(
        account=resource_account, fqdn=fqdn, files=files, path=path
    )

    return providers.filemanager.ls(account=resource_account, fqdn=fqdn, path=path)


@router.get(
    "/{email_or_username}/{instance_type}/{fqdn}/file/{path:path}",
    status_code=201,
    response_model=models.rest.Detail,
    responses={409: {"model": models.rest.Error}, 500: {"model": models.rest.Error}},
)
def create_download_link(
    response: Response,
    email_or_username: str,
    instance_type: str,
    hostname: str,
    path: str = Path(default="."),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account),
):
    fqdn = f"{hostname}.{bearer_account.username}.{instance_type}.cloud.netsoc.co"

    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    download = providers.filemanager.get_download(account=resource_account, path=path)

    request = models.download.Request(
        iat=time.time(), exp=time.time() + 300, obj=download
    )

    response.headers[
        "location"
    ] = f"/v1/files/{email_or_username}/{instance_type}/{fqdn}/download/{request.sign_serialize(config.links.jwt.private_key).token}"


# tar'd directories not yet working
@router.get(
    "/{email_or_username}/{instance_type}/{fqdn}/download/{token}",
    status_code=200,
    response_model=models.rest.Info,
    responses={409: {"model": models.rest.Error}, 500: {"model": models.rest.Error}},
)
def download_backup(
    email_or_username: str,
    hostname: str,
    token: str
):
    try:
        request = models.jwt.Serialized(token=token).deserialize_verify(
            models.download.Request, config.links.jwt.public_key
        )
    except Exception as e:
        logger.error(f"Invalid JWT", token=token, e=e, exc_info=True)

        raise exceptions.rest.Error(
            status_code=400,
            detail=models.rest.Detail(msg="Invalid or expired download token"),
        )

    return providers.filemanager.stream_download(request, fqdn)
