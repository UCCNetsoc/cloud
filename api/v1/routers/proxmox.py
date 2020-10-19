import time
import structlog as logging


from fastapi import APIRouter, HTTPException, Depends, Path
from pydantic import BaseModel, Field

from typing import List, Dict

from v1 import providers, templates, models, exceptions, utilities, templates
from v1.config import config

logger = logging.getLogger(__name__)

router = APIRouter()

def fancy_name(instance_type: models.proxmox.Type) -> str:
    if instance_type == models.proxmox.Type.LXC:
        return "Service"
    elif instance_type == models.proxmox.Type.VPS:
        return "Virtual Private Server"

@router.get(
    '/traefik-config',
    status_code=200,
    response_model=dict,
    responses={400: {"model": models.rest.Error}}
)
async def get_traefik_config():
    return providers.proxmox.build_traefik_config("web-secure")

@router.get(
    '/{email_or_username}/{instance_type}-templates',
    status_code=200,
    response_model=Dict[str,models.proxmox.Template],
    responses={400: {"model": models.rest.Error}}
)
async def get_templates(
    instance_type: models.proxmox.Type
):
    return providers.proxmox.get_templates(instance_type)

@router.post(
    '/{email_or_username}/{instance_type}-request/{hostname}',
    status_code=201,
    responses={400: {"model": models.rest.Error}}
)
async def create_instance_request(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    detail: models.proxmox.RequestDetail,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    # will raise exception if template doesnt exist
    template = providers.proxmox.get_template(instance_type, detail.template_id)

    try:
        instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
        raise exceptions.resource.AlreadyExists(f"Instance {hostname} already exists!")
    except exceptions.resource.NotFound:
        pass

    serialized = models.proxmox.Request(
        exp=time.time() + 172800, # 2 days
        iat=time.time(),
        username=resource_account.username,
        hostname=hostname,
        type=instance_type,
        detail=detail
    ).sign_serialize(config.links.jwt.private_key)

    utilities.webhook.info(
f"""**{resource_account.username} ({resource_account.email}) requested an instance named `{hostname}`!**

They want `{detail.template_id}` for the following reason: ```{detail.reason}```
To approve this request, sign in as a SysAdmin and click the following link: ```{serialized.token}```"""
    )

    providers.email.send(
        [resource_account.email],
        f"{fancy_name(instance_type)} request '{hostname}' received",
        templates.email.netsoc.render(
            heading=f"{fancy_name(instance_type)} request '{hostname}' received",
            paragraph=
            f"""Hi {resource_account.username}!<br/><br/>
                We've received your request for a {fancy_name(instance_type)} named '{hostname}'<br/>
                We will notify you by email as soon as we have approved/denied your request<br/><br/>
                If you do not receive a response within 2-3 days, contact the SysAdmins on the UCC Netsoc Discord<br/>
                Once you make contact, they might request the information below:<br/>
            """,
            embeds=[
                { "text": serialized.token }
            ],
        ),
        "text/html"
    )

@router.post(
    '/{email_or_username}/{instance_type}-request/{hostname}/approval',
    status_code=201,
    responses={400: {"model": models.rest.Error}}
)
async def approve_instance_request(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    serialized: models.jwt.Serialized,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin(bearer_account)

    try:
        providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
        raise exceptions.resource.AlreadyExists(f"Instance {hostname} already exists!")
    except exceptions.resource.NotFound:
        pass

    try:
        request = serialized.deserialize_verify(models.proxmox.Request, config.links.jwt.public_key)
    except Exception as e:
        logger.error(f"Invalid JWT", serialized=serialized, e=e, exc_info=True)

        raise exceptions.rest.Error(status_code=400, detail=models.rest.Detail(
            msg="Invalid or expired request, please ask user to re-request"
        ))
    

    if request.username != resource_account.username:
        raise exceptions.rest.Error(status_code=400, detail=models.rest.Detail(
            msg=f"Token is for a user other than {email_or_username}"
        ))

    if request.hostname != hostname:
        raise exceptions.rest.Error(status_code=400, detail=models.rest.Detail(
            msg=f"Token is for a hostname other than {hostname}"
        ))


    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email}) request for an instance named `{hostname}` was granted! Installing...**"""
    )

    providers.proxmox.create_instance(
        instance_type,
        resource_account,
        hostname,
        request.detail
    )

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email})'s instance `{hostname}` was installed!**"""
    )

    providers.email.send(
        [resource_account.email],
        f"{fancy_name(instance_type)} request '{hostname}' accepted!",
        templates.email.netsoc.render(
            heading=f"{fancy_name(instance_type)} request '{hostname}' accepted",
            paragraph=
            f"""Hi {resource_account.username}!<br/><br/>
                We received your request for a {fancy_name(instance_type)} named '{hostname}'<br/>
                We're delighted to inform you that your request has been granted!<br/><br/>
                <br/>
                <br/>
            """
        ),
        "text/html"
    )

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email})'s instance `{hostname}` was emailed about installation details!**"""
    )
    

@router.post(
    '/{email_or_username}/{instance_type}-request/{hostname}/denial',
    status_code=201,
    responses={400: {"model": models.rest.Error}}
)
async def deny_instance_request(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    serialized: models.jwt.Serialized,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin(bearer_account)

    try:
        request = serialized.deserialize_verify(models.proxmox.Request, config.links.jwt.public_key)
    except Exception as e:
        logger.error(f"Invalid JWT", serialized=serialized, e=e, exc_info=True)

        raise exceptions.rest.Error(status_code=400, detail=models.rest.Detail(
            msg="Invalid or expired request, please ask user to re-request"
        ))
    

    if request.username != resource_account.username:
        raise exceptions.rest.Error(status_code=400, detail=models.rest.Detail(
            msg=f"Token is for a user other than {email_or_username}"
        ))

    if request.hostname != hostname:
        raise exceptions.rest.Error(status_code=400, detail=models.rest.Detail(
            msg=f"Token is for a hostname other than {hostname}"
        ))


    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email}) request for a instance named `{hostname}` was denied!**"""
    )

    providers.email.send(
        [resource_account.email],
        f"{fancy_name(instance_type)} request '{hostname}' denied",
        templates.email.netsoc.render(
            heading=f"{fancy_name(instance_type)} request '{hostname}' denied",
            paragraph=
            f"""Hi {resource_account.username}!<br/><br/>
                We received your request for a {fancy_name(instance_type)} named '{hostname}'<br/>
                Unfortunately we've had to deny the request for now.<br/><br/>
                Requests for {fancy_name(instance_type)}s are typically denied where we believe a Terms of Service violation may occur, or that a {fancy_name(instance_type)} may not be suitable for the reason specified<br/>
                If you have any questions, contact the SysAdmins on the UCC Netsoc Discord<br/>
            """
        ),
        "text/html"
    )
    
@router.get(
    '/{email_or_username}/{instance_type}',
    status_code=200,
)
async def get_instances(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    return providers.proxmox.read_instances_by_account(instance_type, resource_account)

@router.post(
    '/{email_or_username}/{instance_type}/{hostname}/start',
    status_code=201,
)
async def start_instance(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    providers.proxmox.start_instance(instance)

@router.post(
    '/{email_or_username}/{instance_type}/{hostname}/stop',
    status_code=200,
)
async def stop_instance(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    providers.proxmox.stop_instance(instance)

@router.post(
    '/{email_or_username}/{instance_type}/{hostname}/shutdown',
    status_code=200,
)
async def shutdown_instance(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    providers.proxmox.shutdown_instance(instance)

@router.post(
    '/{email_or_username}/{instance_type}/{hostname}/active',
    status_code=201,
)
async def mark_instance_active(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    providers.proxmox.mark_instance_active(instance)

@router.delete(
    '/{email_or_username}/{instance_type}/{hostname}',
    status_code=200,
)
async def delete_instance(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    providers.proxmox.delete_instance(instance)


ranged_port = models.proxmox.generate_ranged_port_field_args(config.proxmox.port_forward.range[0], config.proxmox.port_forward.range[1])

@router.post(
    '/{email_or_username}/{instance_type}/{hostname}/port/{external_port}/{internal_port}',
    status_code=200,
)
async def add_instance_port(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    external_port: int = Path(**ranged_port),
    internal_port: int = Path(**models.proxmox.Port),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    providers.proxmox.add_instance_port(instance, external_port, internal_port)

@router.delete(
    '/{email_or_username}/{instance_type}/{hostname}/port/{external_port}',
    status_code=200,
)
async def remove_instance_port(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    external_port: int = Path(**models.proxmox.Port), # don't need to worry about them deleting non-ranged ports
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    providers.proxmox.remove_instance_port(instance, external_port)

@router.post(
    '/{email_or_username}/{instance_type}/{hostname}/vhost/{vhost}',
    status_code=200,
)
async def add_instance_vhost(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    vhost: str = Path(**models.proxmox.VHost),
    options: models.proxmox.VHostOptions = models.proxmox.VHostOptions(),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    providers.proxmox.add_instance_vhost(instance, vhost, options)

@router.delete(
    '/{email_or_username}/{instance_type}/{hostname}/vhost/{vhost}',
    status_code=200,
)
async def remove_instance_vhost(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    vhost: str = Path(**models.proxmox.VHost),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    providers.proxmox.remove_instance_vhost(instance, vhost)


@router.post(
    '/{email_or_username}/{instance_type}/{hostname}/reset-root-user',
    status_code=200,
    response_model=models.rest.Info
)
async def reset_instance_root_user(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
) -> models.rest.Info:
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    password, private_key = providers.proxmox.reset_instance_root_user(instance)

    providers.email.send(
        [resource_account.email],
        f"{fancy_name(instance_type)} '{hostname}' root password reset",
        templates.email.netsoc.render(
            heading=f"{fancy_name(instance_type)} '{hostname}' root password reset",
            paragraph=f"""Hi {resource_account.username}!<br/><br/>
                We successfully reset the password and SSH identity for the root user on your {fancy_name(instance_type)} named '{hostname}'<br/>
                You will find them the password followed by the SSH private key below:<br/><br/>
            """,
            embeds=[
                { "text": password },
                { "text": private_key }
            ]
        ),
        "text/html"
    )

    return models.rest.Info(
        detail=models.rest.Detail(
            msg="A new password and private key have been sent to the email associated with the account"
        )
    )
