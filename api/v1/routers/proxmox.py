import os
import time
import structlog as logging


from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Path, Query, Response, UploadFile, File
from fastapi.responses import StreamingResponse

from pydantic import BaseModel, Field

from typing import List, Dict, Optional

from v1 import providers, templates, models, exceptions, utilities, templates
from v1.config import config

logger = logging.getLogger(__name__)

router = APIRouter()

def fancy_name(instance_type: models.proxmox.Type) -> str:
    if instance_type == models.proxmox.Type.LXC:
        return "Container"
    elif instance_type == models.proxmox.Type.VPS:
        return "VPS"

def fancy_specs(specs: models.proxmox.Specs) -> str:
    return f"{specs.cores} CPU, {specs.memory}MB RAM, {specs.disk_space}GB disk space, {specs.swap}MB swap"

def ensure_active(instance: models.proxmox.Instance):
    """Throws exception saying instance must be active to perform action if instance is not active"""

    if instance.active == False:
        raise exceptions.rest.Error(status_code=403, detail=models.rest.Detail(
            msg="Instance must be activated to perform this action"
        ))

def ensure_not_tos_suspended(instance: models.proxmox.Instance):
    """Throws exception saying instance must be not suspended"""

    if instance.metadata.tos.suspended == True:
        raise exceptions.rest.Error(status_code=403, detail=models.rest.Detail(
            msg=f"Instance is suspended for Terms of Service violations ({metadata.tos.reason})"
        ))

@router.get(
    '/traefik-config',
    status_code=200,
    response_model=dict,
    responses={400: {"model": models.rest.Error}}
)
def get_traefik_config(
    key: str = ""
):
    if key != config.proxmox.network.traefik.config_key:
        raise exceptions.rest.Error(status_code=403, detail=models.rest.Detail(
            msg=f"invalid config key"
        ))


    return providers.proxmox.build_traefik_config("web-secure")

@router.get(
    '/{email_or_username}/{instance_type}-templates',
    status_code=200,
    response_model=Dict[str,models.proxmox.Template],
    responses={400: {"model": models.rest.Error}}
)
def get_templates(
    instance_type: models.proxmox.Type
):
    return providers.proxmox.read_templates(instance_type)

@router.get(
    '/{email_or_username}/{instance_type}-template/{template_id}',
    status_code=200,
    response_model=models.proxmox.Template,
    responses={400: {"model": models.rest.Error}}
)
def get_template(
    instance_type: models.proxmox.Type,
    template_id: str = Path(**models.proxmox.TemplateID)
):
    return providers.proxmox.read_template(instance_type, template_id)


@router.post(
    '/{email_or_username}/{instance_type}-request/{hostname}',
    status_code=201,
    responses={400: {"model": models.rest.Error}}
)
def create_instance_request(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    detail: models.proxmox.InstanceRequestDetail,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    # will raise exception if template doesnt exist
    template = providers.proxmox.read_template(instance_type, detail.template_id)

    try:
        instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
        raise exceptions.resource.AlreadyExists(f"Instance {hostname} already exists!")
    except exceptions.resource.NotFound:
        pass

    serialized = models.proxmox.InstanceRequest(
        exp=time.time() + 172800, # 2 days
        iat=time.time(),
        username=resource_account.username,
        hostname=hostname,
        type=instance_type,
        detail=detail
    ).sign_serialize(config.links.jwt.private_key)

    utilities.webhook.info(
f"""**{resource_account.username} ({resource_account.email}) requested an instance named `{hostname}`!**

They want **{template.metadata.title} {fancy_name(instance_type)} ({fancy_specs(template.specs)})** for the following reason: ```{detail.reason}```
To approve this request, sign in as a SysAdmin and click the following link:
{config.links.base_url}/instance-request/{resource_account.username}/{instance_type}-request/{hostname}/{serialized.token}
"""
    )

    # providers.email.send(
    #     [resource_account.email],
    #     f"{fancy_name(instance_type)} request '{hostname}' received",
    #     templates.email.netsoc.render(
    #         heading=f"{fancy_name(instance_type)} request '{hostname}' received",
    #         paragraph=
    #         f"""Hi {resource_account.username}!<br/><br/>
    #             We've received your request for a {fancy_name(instance_type)} named '{hostname}'<br/>
    #             We will notify you by email as soon as we have approved/denied your request<br/><br/>
    #             If you do not receive a response within 2-3 days, contact the SysAdmins on the UCC Netsoc Discord<br/>
    #             Once you make contact, they might request the information below:<br/>
    #         """,
    #         embeds=[
    #             { "text": serialized.token }
    #         ],
    #     ),
    #     "text/html"
    # )

    return models.rest.Info(
        detail=models.rest.Detail(
            msg="Instance request received, the email associated with this account will be notified as soon as the request has been approved/denied"
        )
    )


@router.get(
    '/{email_or_username}/{instance_type}-request/{hostname}',
    status_code=200,
    response_model=models.proxmox.InstanceRequest
)
def get_instance_request(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    token: str,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin(bearer_account)

    serialized = models.jwt.Serialized(token=token)

    try:
        request = serialized.deserialize_verify(models.proxmox.InstanceRequest, config.links.jwt.public_key)
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

    
    return request

@router.post(
    '/{email_or_username}/{instance_type}-request/{hostname}/approval',
    status_code=201,
    responses={400: {"model": models.rest.Error}}
)
def approve_instance_request(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    token: str,
    background_tasks: BackgroundTasks,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account),
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin(bearer_account)

    try:
        providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
        raise exceptions.resource.AlreadyExists(f"Instance {hostname} already exists!")
    except exceptions.resource.NotFound:
        pass

    serialized = models.jwt.Serialized(token=token)

    try:
        request = serialized.deserialize_verify(models.proxmox.InstanceRequest, config.links.jwt.public_key)
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

    def creation_task():
        try:
            providers.proxmox.create_instance(
                instance_type,
                resource_account,
                hostname,
                request.detail
            )

            providers.email.send(
                [resource_account.email],
                f"{fancy_name(instance_type)} request '{hostname}' accepted!",
                templates.email.netsoc.render(
                    heading=f"{fancy_name(instance_type)} request '{hostname}' accepted",
                    paragraph=
                    f"""Hi {resource_account.username}!<br/><br/>
                        We received your request for a {fancy_name(instance_type)} named '{hostname}'<br/>
                        We're delighted to inform you that your instance request has been granted!<br/>
                        For guides on how to SSH into your instance, please consult the <a style="color: white" href='https://tutorial.netsoc.co'>tutorial</a>
                        <br/>
                    """
                ),
                "text/html"
            )

            utilities.webhook.info(
                f"""**{resource_account.username} ({resource_account.email})'s instance `{hostname}` was emailed about installation!**"""
            )

        except Exception as e:
            utilities.webhook.info(
                f"""**{resource_account.username} ({resource_account.email})'s instance `{hostname}` install task failed: ```{e}```!**"""
            )
            raise e

        utilities.webhook.info(
            f"""**{resource_account.username} ({resource_account.email})'s instance `{hostname}` was installed!**"""
        )

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email}) request for an instance named `{hostname}` was granted! Install job started...**"""
    )
    background_tasks.add_task(creation_task)
    

@router.post(
    '/{email_or_username}/{instance_type}-request/{hostname}/denial',
    status_code=201,
    responses={400: {"model": models.rest.Error}}
)
def deny_instance_request(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    token: str,
    request_denial: models.proxmox.InstanceRequestDenial,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin(bearer_account)

    serialized = models.jwt.Serialized(token=token)

    try:
        request = serialized.deserialize_verify(models.proxmox.InstanceRequest, config.links.jwt.public_key)
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
        f"""**{resource_account.username} ({resource_account.email}) request for a instance named `{hostname}` was denied!**
            The reason given was: ```{request_denial.reason}```
        """
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
                Requests for {fancy_name(instance_type)}s are typically denied where we believe a ToS violation may occur, or that a {fancy_name(instance_type)} may not be suitable for the reason you specified<br/><br/>
                The reason your request was denied is available below<br/><br/>
                If you have any questions, contact the SysAdmins on the UCC Netsoc Discord<br/>
            """,
            embeds=[
                { "text": request_denial.reason }
            ]   
        ),
        "text/html"
    )

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email}) was emailed about denial!**"""
    )
    
@router.get(
    '/{email_or_username}/{instance_type}',
    status_code=200,
)
def get_instances(
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
def start_instance(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    ensure_active(instance)

    providers.proxmox.start_instance(instance)

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email}) started instance `{instance.hostname}`!**"""
    )

@router.post(
    '/{email_or_username}/{instance_type}/{hostname}/stop',
    status_code=200,
)
def stop_instance(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    ensure_active(instance)

    providers.proxmox.stop_instance(instance)

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email}) stopped instance `{instance.hostname}`!**"""
    )

@router.post(
    '/{email_or_username}/{instance_type}/{hostname}/shutdown',
    status_code=200,
)
def shutdown_instance(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    ensure_active(instance)

    providers.proxmox.shutdown_instance(instance)

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email}) shutdown instance `{instance.hostname}`!**"""
    )

@router.post(
    '/{email_or_username}/{instance_type}/{hostname}/respec-request',
    status_code=201,
)
def request_instance_respec(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    respec: models.proxmox.RespecRequest,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    ensure_active(instance)

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email}) requested new specifications for `{instance.hostname}`!**```{respec.details}```"""
    )


@router.post(
    '/{email_or_username}/{instance_type}/{hostname}/active',
    status_code=201,
)
def mark_instance_active(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    ensure_not_tos_suspended(instance)
    providers.proxmox.mark_instance_active(instance)

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email}) marked instance `{instance.hostname}` active!**"""
    )

@router.delete(
    '/{email_or_username}/{instance_type}/{hostname}',
    status_code=200,
)
def delete_instance(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    ensure_active(instance)
    
    providers.proxmox.delete_instance(instance)

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email}) deleted instance `{instance.hostname}`**"""
    )


ranged_port = models.proxmox.generate_ranged_port_field_args(config.proxmox.network.port_forward.range[0], config.proxmox.network.port_forward.range[1])

@router.post(
    '/{email_or_username}/{instance_type}/{hostname}/port/{external_port}/{internal_port}',
    status_code=200,
)
def add_instance_port(
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
    ensure_active(instance)

    providers.proxmox.add_instance_port(instance, external_port, internal_port)

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email}) added instance `{instance.hostname}` portmap {external_port}->{internal_port}**"""
    )

@router.get(
    '/{email_or_username}/{instance_type}/{hostname}/free-external-port',
    status_code=200,
    response_model=int
)
def get_random_available_external_port(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname)
):
    return providers.proxmox.get_random_available_external_port()

@router.delete(
    '/{email_or_username}/{instance_type}/{hostname}/port/{external_port}',
    status_code=200,
)
def remove_instance_port(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    external_port: int = Path(**models.proxmox.Port), # don't need to worry about them deleting non-ranged ports
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    ensure_active(instance)

    providers.proxmox.remove_instance_port(instance, external_port)

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email}) removed instance `{instance.hostname}` portmap for external port {external_port}**"""
    )

@router.get(
    '/vhost-requirements',
    status_code=200,
    response_model=models.config.Proxmox.Network.VHostRequirements
)
def get_allowed_a_aaaa() -> str:
    return config.proxmox.network.vhosts


@router.post(
    '/{email_or_username}/{instance_type}/{hostname}/vhost/{vhost}',
    status_code=200,
)
def add_instance_vhost(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    options: models.proxmox.VHostOptions,
    hostname: str = Path(**models.proxmox.Hostname),
    vhost: str = Path(**models.proxmox.VHost),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    ensure_active(instance)

    providers.proxmox.add_instance_vhost(instance, vhost, options)

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email}) added instance `{instance.hostname}` vhost {vhost}**"""
    )

@router.delete(
    '/{email_or_username}/{instance_type}/{hostname}/vhost/{vhost}',
    status_code=200,
)
def remove_instance_vhost(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    hostname: str = Path(**models.proxmox.Hostname),
    vhost: str = Path(**models.proxmox.VHost),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    ensure_active(instance)

    providers.proxmox.remove_instance_vhost(instance, vhost)

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email}) deleted instance `{instance.hostname}` vhost {vhost}**"""
    )


@router.post(
    '/{email_or_username}/{instance_type}/{hostname}/reset-root-user',
    status_code=200,
    response_model=models.rest.Info
)
def reset_instance_root_user(
    email_or_username: str,
    instance_type: models.proxmox.Type,
    background_tasks: BackgroundTasks,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
) -> models.rest.Info:
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    instance = providers.proxmox.read_instance_by_account(instance_type, resource_account, hostname)
    ensure_active(instance)

    def reset_password_task():
        try:
            password, private_key, root_user = providers.proxmox.reset_instance_root_user(instance)
        
            providers.email.send(
                [resource_account.email],
                f"{fancy_name(instance_type)} '{hostname}' root user information",
                templates.email.netsoc.render(
                    heading=f"{fancy_name(instance_type)} '{hostname}' root user information",
                    paragraph=f"""Hi {resource_account.username}!<br/><br/>
                        We successfully set the password and SSH identity for the root user on your {fancy_name(instance_type)} named '{hostname}'<br/><br/>
                        You will find the password followed by the SSH private key for the user <code>root</code> below:<br/>
                    """,
                    embeds=[
                        { "text": f"<code>{password}</code>" },
                        { "text": f"<pre>{private_key}</pre>" }
                    ]
                ),
                "text/html"
            )

        except Exception as e:
            utilities.webhook.info(
                f"""**{resource_account.username} ({resource_account.email})'s instance `{hostname}` reset password task failed: ```{e}```!**"""
            )
            raise e

        utilities.webhook.info(
            f"""**{resource_account.username} ({resource_account.email}) reset instance `{instance.hostname}` root user**"""
        )

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email}) reset instance `{instance.hostname}` root user task started...**"""
    )
    background_tasks.add_task(reset_password_task)

    return models.rest.Info(
        detail=models.rest.Detail(
            msg="A new root password and private key will be sent to the email associated with this account. If you do not receive it, contact the SysAdmins"
        )
    )