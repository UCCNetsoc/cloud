import time
import traceback
import string
import random

from fastapi import APIRouter, HTTPException, Depends, Path
from pydantic import BaseModel

from typing import List

from v1 import providers, templates, models, exceptions, utilities
from v1.config import config

router = APIRouter()

@router.get(
    '/{email_or_username}/databases/',
    status_code=200,
    response_model=List[models.mysql.Database]  
)
async def list_databases(
    email_or_username: str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    return providers.mysql.list_by_account(resource_account)


@router.post(
    '/{email_or_username}/databases/{name}',
    status_code=201,
    response_model=models.rest.Info 
)
async def create_database(
    email_or_username: str,
    name: str = Path(**models.mysql.Name),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    providers.mysql.create_database(resource_account, models.mysql.Database(
        name=name
    ))

    utilities.webhook.info(f"**Created database** - {name} - {resource_account.username} ({resource_account.email})")

    return models.rest.Info(
        detail=models.rest.Detail(
            msg=f"MySQL database {name} created"
        )
    )


@router.delete(
    '/{email_or_username}/databases/{name}',
    status_code=200,
    response_model=models.rest.Info
)
async def delete_database(
    email_or_username: str,
    name: str = Path(**models.mysql.Name),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    providers.mysql.delete_database(resource_account, models.mysql.Database(
        name=name
    ))

    utilities.webhook.info(f"**Deleted database** - {name} - {resource_account.username} ({resource_account.email})")

    return models.rest.Info(
        detail=models.rest.Detail(
            msg=f"MySQL database {name} deleted"
        )
    )

@router.get(
    '/{email_or_username}/user',
    status_code=200
)
async def get_mysql_user(
    email_or_username: str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    if providers.mysql.account_user_exists(resource_account):
        return
    else:
        raise exceptions.rest.Error(
            404,
            models.rest.Detail(
                msg="No MySQL user"
            )
        )

@router.post(
    '/{email_or_username}/user',
    status_code=201,
    response_model=models.rest.Info
)
async def create_mysql_user(
    email_or_username: str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    if providers.mysql.account_user_exists(resource_account):
        raise exceptions.rest.Error(
            400,
            models.rest.Detail(
                msg="MySQL user already exists"
            )
        )
    else:
        chars = string.ascii_letters + string.digits
        password = "".join(random.choice(chars) for _ in range(20))

        providers.mysql.create_account_user(resource_account, password)

        utilities.webhook.info(f"**Created MySQL user** - {resource_account.username} ({resource_account.email})")

        return models.rest.Info(
            detail = models.rest.Detail(
                msg="MySQL user created."
            )
        )


@router.post(
    '/{email_or_username}/user/password-reset-email',
    status_code=201,
    response_model=models.rest.Info
)
async def send_mysql_user_password_reset_email(
    email_or_username: str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    chars = string.ascii_letters + string.digits
    password = "".join(random.choice(chars) for _ in range(24))

    providers.mysql.change_password(resource_account, password)

    providers.email.send(
        [resource_account.email],
        'MySQL User Password',
        templates.email.netsoc.render(
            heading="MySQL User Password",
            paragraph=f"""Hi {resource_account.username}!<br/><br/>Your MySQL user <code style="margin-left: 4px;margin-right:4px">{resource_account.username}</code>'s password has been (re)set!<br/>
                The password for your user is now:""",
            embeds=[
                { "text": password }
            ],
        ),
        "text/html"
    )

    utilities.webhook.info(f"**(Re)set MySQL user password** - {resource_account.username} ({resource_account.email})")

    return models.rest.Info(
        detail=models.rest.Detail(
            msg="The new MySQL user password has been sent to the email address associated with the account"
        )
    )


