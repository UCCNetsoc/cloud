
import time

from typing import List
from fastapi import APIRouter, Response, Depends, Path
from fastapi.responses import StreamingResponse

from v1 import providers, models, utilities
from v1.config import config

router = APIRouter()

@router.get(
    '/{email_or_username}/',
    status_code=200,
    response_model=List[models.backup.Backup],
)
def get_user_backups(
    email_or_username: str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    return providers.backups.list_by_account(resource_account)

@router.post(
    '/{email_or_username}/{backup_name}/download-link',
    status_code=201,
    response_model=models.rest.Info,
    responses={409: {"model": models.rest.Error}, 500: {"model": models.rest.Error}}
)
def create_backup_download_link(
    response: Response,
    email_or_username: str,
    backup_name: str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    backup = providers.backups.read_by_account(resource_account, backup_name)
    request = models.backup.Request(
        iat=time.time(),
        exp=time.time() + 300,
        backup=backup
    )

    response.headers["location"] = f"/v1/backups/{email_or_username}/{backup_name}/download/{request.sign_serialize(config.links.jwt.private_key).token}"

    utilities.webhook.info(f"**Requested backup download link** - {resource_account.username} ({resource_account.email})")


@router.get(
    '/{email_or_username}/{backup_name}/download/{token}',
    status_code=200,
    response_model=models.rest.Info,
    responses={409: {"model": models.rest.Error}, 500: {"model": models.rest.Error}}
)
def download_backup(
    email_or_username: str,
    backup_name: str,
    token: str
):
    request = models.jwt.Serialized(token=token).deserialize_verify(models.backup.Request, config.links.jwt.public_key)

    # utilities.webhook.info(f"**Downloaded backup** - uid {request.uid}")

    return providers.backups.stream_backup(request.backup)