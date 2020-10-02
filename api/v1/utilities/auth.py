
import structlog

from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from pydantic import ValidationError
from typing import List

from v1 import exceptions, models, providers
from v1.config import config

#log.info("Direct Grant URL Setup", url=config.get().jwt.direct_grant_url)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=config.auth.direct_grant_url,
    scopes={
        "profile": "Profile",
        "openid": "OpenID",
        "email": "Email",
        "roles": "Role list"
    }
)

async def decode_access_token(token: str = Depends(oauth2_scheme)) -> models.jwt.EmailToken:
    try:
        return models.jwt.Serialized(token=token).deserialize_verify(models.jwt.EmailToken, config.auth.jwt.public_key)
    except ValidationError as v:
        raise exceptions.rest.Error(
            401,
            models.rest.Detail(
                msg="Unknown JWT format"
            )
        )
    except Exception as e:
        raise exceptions.rest.Error(
            401, 
            models.rest.Detail(
                msg=f"Invalid Bearer token: {e}"
            )
        )

async def get_bearer_account(
    email_token = Depends(decode_access_token)
) -> models.account.Account:
    if providers.accounts.email_exists(email_token.email):
        return providers.accounts.read_account_by_email(email_token.email)
    else:
        raise exceptions.rest.Error(
            401, 
            models.rest.Detail(
                msg=f"No such account for given Bearer token"
            )
        )

def ensure_sysadmin_or_acting_on_self(
    bearer_account: models.account.Account,
    resource_account: models.account.Account
):
    """
    Raises an Unauthorized exception if the Bearer account (i.e the currently logged in user) is modifying an account other than itself

    If the bearer user is a SysAdmin, this check is ignored
    """
    for groupname, group in bearer_account.groups.items():
        if group.gid == models.group.NetsocSysAdmin.gid:
            return

    if resource_account is None or resource_account.uid != bearer_account.uid:
        raise exceptions.rest.Error(
            401, 
            models.rest.Detail(
                msg=f"You do not have permission to access this resource"
            )
        )
    
