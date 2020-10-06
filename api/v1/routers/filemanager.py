
from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse

import time
import os
from pathlib import Path
from typing import List, Optional, Dict
from v1 import providers, models, utilities, exceptions
from v1.config import config

import structlog as logging

logger = logging.getLogger(__name__)
logger.info(f"", providers=providers)
router = APIRouter()

@router.get(
    '/{email_or_username}/ls/{path:path}',
    status_code=200,
    response_model = Dict[str, Dict]
)
def list_directory_contents(
    email_or_username: str,
    path: Optional[str],
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)
    if path == None or path == "":
        path = "."
    return providers.filemanager.ls(resource_account, path)

@router.get(
    '/{email_or_username}/stat/{path:path}',
    status_code=200,
    response_model = Dict[str, List]
)
def stat_path(
    email_or_username: str,
    path: str=Path(default="/"),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    return providers.filemanager.stat(
        account=resource_account,
        path=path,
    )

@router.get(
    '/{email_or_username}/file/{path:path}',
    status_code=201,
    response_model=models.rest.Detail,
    responses={409: {"model": models.rest.Error}, 500: {"model": models.rest.Error}}
)
def create_download_link(
    response: Response,
    email_or_username: str,
    path: str=Path(default="."),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    download = providers.filemanager.get_download(resource_account, path)
    request = models.download.Request(
        iat=time.time(),
        exp=time.time() + 300,
        obj=download
    )

    response.headers["location"] = f"/v1/files/{email_or_username}/download/{request.sign_serialize(config.links.jwt.private_key).token}"

@router.get(
    '/{email_or_username}/download/{token}',
    status_code=200,
    response_model=models.rest.Info,
    responses={409: {"model": models.rest.Error}, 500: {"model": models.rest.Error}}
)
def download_backup(
    email_or_username: str,
    token: str
):
    try:
        request = models.jwt.Serialized(token=token).deserialize_verify(models.download.Request, config.links.jwt.public_key)
    except Exception as e:
        logger.error(f"Invalid JWT", token=token, e=e, exc_info=True)

        raise exceptions.rest.Error(status_code=400, detail=models.rest.Detail(
            msg="Invalid or expired download token"
        ))

    #utilities.webhook.info(f"**Downloaded backup** - uid {request.uid}")
    return providers.filemanager.stream_download(request)
