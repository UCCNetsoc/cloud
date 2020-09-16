from fastapi import APIRouter, HTTPException, Depends, Path
from pydantic import constr, EmailStr, Field
from typing import Union, List, Dict
from starlette.responses import JSONResponse

import time

from v1 import models, exceptions, providers, utilities

router = APIRouter()

# @router.get(
#     '/',
#     status_code=200,
#     response_model=Dict[str,List[models.website.Website]],
#     responses={400: {"model": models.rest.Error}}
# )
# def get_websites():

#     return providers.websites.read_all()

@router.get(
    '/{email_or_username}',
    status_code=200,
    response_model=Dict[str, models.website.Website],
    responses={400: {"model": models.rest.Error}}
)
def get_user_websites(
    email_or_username : str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    return providers.websites.read_all_by_account(resource_account)

@router.post(
    '/{email_or_username}/{name}',
    status_code=201,
    responses={400: {"model": models.rest.Error}}
)
async def create_website(
    email_or_username : str,
    name: str = Path(**models.website.Name),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    providers.websites.create_website(resource_account, name)

    utilities.webhook.info(f"**Created website** - {name} - {resource_account.username} ({resource_account.email})")

@router.delete(
    '/{email_or_username}/{name}',
    status_code=201,
    responses={400: {"model": models.rest.Error}}
)
async def delete_website(
    email_or_username : str,
    name: str = Path(**models.website.Name),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    website = providers.websites.read_by_account(resource_account, name)
    providers.websites.delete_website(website)

    utilities.webhook.info(f"**Deleted website** - {name} - {resource_account.username} ({resource_account.email})")


@router.post(
    '/{email_or_username}/{name}/host/{host}',
    status_code=201,
    responses={400: {"model": models.rest.Error}}
)
def add_website_host(
    email_or_username : str,
    name : str = Path(**models.website.Name),
    host : str = Path(**models.website.Host),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    website = providers.websites.read_by_account(resource_account, name)

    if host in website.config.hosts:
        raise exceptions.rest.Error(
            400,
            models.rest.Detail(
                msg=f"Website does already has host {host}"
            )
        )

    website.config.hosts.add(host)
    providers.websites.write_out_website_config(website)

    utilities.webhook.info(f"**Added website host** - {name} - {host} - {resource_account.username} ({resource_account.email})")


@router.delete(
    '/{email_or_username}/{name}/host/{host}',
    status_code=200,
    responses={400: {"model": models.rest.Error}}
)
def delete_website_host(
    email_or_username : str,
    name : str = Path(**models.website.Name),
    host : str = Path(**models.website.Host),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    website = providers.websites.read_by_account(resource_account, name)
    
    if host not in website.config.hosts:
        raise exceptions.rest.Error(
            400,
            models.rest.Detail(
                msg=f"Website does not have host {host}"
            )
        )

    website.config.hosts.remove(host)
    providers.websites.write_out_website_config(website)

    utilities.webhook.info(f"**Deleted website host** - {name} - {host} - {resource_account.username} ({resource_account.email})")


@router.post(
    '/{email_or_username}/{name}/software/{software}',
    status_code=201,
    responses={400: {"model": models.rest.Error}}
)
def install_website_software(
    software : models.website.Software,
    args: models.website.SoftwareArgs,
    email_or_username : str,
    name : str = Path(**models.website.Name),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    website = providers.websites.read_by_account(resource_account, name)

    providers.websites.install_software(website, software, args)

    utilities.webhook.info(f"**Installed website software** - {name} - {software} - {resource_account.username} ({resource_account.email})")

@router.delete(
    '/{email_or_username}/{name}/software',
    status_code=200,
    responses={400: {"model": models.rest.Error}}
)
def uninstall_website_software(
    email_or_username : str,
    name : str = Path(**models.website.Name),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    website = providers.websites.read_by_account(resource_account, name)
    providers.websites.uninstall_software(website)

    utilities.webhook.info(f"**Uninstalled website software** - {name} - {website.software} - {resource_account.username} ({resource_account.email})")
