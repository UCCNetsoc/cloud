
from fastapi import APIRouter, Path, Depends, Response
from fastapi.responses import StreamingResponse

import time
from v1 import providers, models, utilities, exceptions
from v1.config import config

import structlog as logging

logger = logging.getLogger(__name__)
logger.info(f"", providers=providers)

router = APIRouter()

@router.get(
    '/files/{email_or_username}/ls/{path}',
    status_code=200,
    response_model=models.filebrowser.FileList
)
def list_directory_contents(
    email_or_username: str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

@router.get(
    'files/{email_or_username}/file/{path}',
    status_code=201,
    response_model=models.rest.Detail,
    responses={409: {"model": models.rest.Error}, 500: {"model": models.rest.Error}}
)
def create_download_link(
    response: Response,
    email_or_username: str,
    path: str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    download = providers.filemanager.get_download(resource_account, path)
    request = models.filemanager.Request(
        iat=time.time(),
        exp=time.time() + 300,
        download=download
    )

    response.headers["location"] = f"/v1/files/{email_or_username}/download/{request.sign_serialize(config.links.jwt.private_key).token}"

@router.get(
    'files/{email_or_username}/file/{path}/{token}',
    status_code=200,
    response_model=models.rest.Info,
    responses={409: {"model": models.rest.Error}, 500: {"model": models.rest.Error}}
)
def stream_download(
    email_or_username: str,
    token: str
):
    try:
        request = models.jwt.Serialized(token=token).deserialize_verify(models.filemanager.Request, config.links.jwt.public_key)
    except Exception as e:
        logger.error(f"Invalid JWT", token=token, e=e, exc_info=True)

        raise exceptions.rest.Error(status_code=400, detail=models.rest.Detail(
            msg="Invalid or expired download token"
        ))

    return providers.backups.stream_download(request.download)
