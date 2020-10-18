import time
import structlog as logging


from fastapi import APIRouter, HTTPException, Depends, Path
from pydantic import BaseModel, Field

from typing import List, Dict

from v1 import providers, templates, models, exceptions, utilities, templates
from v1.config import config

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    '/lxc-templates',
    status_code=200,
    response_model=Dict[str,models.proxmox.Template],
    responses={400: {"model": models.rest.Error}}
)
async def get_lxc_templates():
    return config.proxmox.lxc.templates

@router.post(
    '/lxc-request/{email_or_username}/{hostname}',
    status_code=201,
    responses={400: {"model": models.rest.Error}}
)
async def create_lxc_request(
    email_or_username: str,
    detail: models.proxmox.RequestDetail,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    if detail.template_id not in config.proxmox.lxc.templates:
        raise exceptions.rest.Error(
            400,
            models.rest.Detail(
                msg=f"LXC template {detail.template_id} does not exist!"
            )
        )

    try:
        lxc = providers.proxmox.read_lxc_by_account(resource_account, hostname)
        raise exceptions.resource.AlreadyExists(f"LXC {hostname} already exists!")
    except exceptions.resource.NotFound:
        pass

    serialized = models.proxmox.LXCRequest(
        exp=time.time() + 172800, # 2 days
        iat=time.time(),
        username=resource_account.username,
        hostname=hostname,
        detail=detail
    ).sign_serialize(config.links.jwt.private_key)

    utilities.webhook.info(
f"""**{resource_account.username} ({resource_account.email}) requested a LXC named `{hostname}`!**

They want `{detail.template_id}` for the following reason: ```{detail.reason}```
To approve this request, sign in as a SysAdmin and click the following link: ```{serialized.token}```"""
    )

    providers.email.send(
        [resource_account.email],
        f"Linux Container '{hostname}' requested",
        templates.email.netsoc.render(
            heading=f"Linux Container '{hostname}'",
            paragraph=
            f"""Hi {resource_account.username}!<br/><br/>
                We've received your request for a Linux Container (LXC) named '{hostname}'<br/>
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
    '/lxc-request/{email_or_username}/{hostname}/approval',
    status_code=201,
    responses={400: {"model": models.rest.Error}}
)
async def approve_lxc_request(
    email_or_username: str,
    serialized: models.jwt.Serialized,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin(bearer_account)

    try:
        lxc = providers.proxmox.read_lxc_by_account(resource_account, hostname)
        raise exceptions.resource.AlreadyExists(f"LXC {hostname} already exists!")
    except exceptions.resource.NotFound:
        pass

    try:
        request = serialized.deserialize_verify(models.proxmox.LXCRequest, config.links.jwt.public_key)
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
        f"""**{resource_account.username} ({resource_account.email}) request for a LXC named `{hostname}` was granted! Installing...**"""
    )

    providers.proxmox.create_lxc(
        resource_account,
        hostname,
        request.detail
    )

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email})'s LXC `{hostname}` was installed!**"""
    )

    providers.email.send(
        [resource_account.email],
        f"Linux Container '{hostname}' request accepted!",
        templates.email.netsoc.render(
            heading=f"Linux Container - '{hostname}' ",
            paragraph=
            f"""Hi {resource_account.username}!<br/><br/>
                We received your request for a Linux Container (LXC) named '{hostname}'<br/>
                We're delighted to inform you that your request has been granted!<br/><br/>
                <br/>
                <br/>
            """
        ),
        "text/html"
    )

    utilities.webhook.info(
        f"""**{resource_account.username} ({resource_account.email})'s LXC `{hostname}` was emailed about installation details!**"""
    )
    

@router.post(
    '/lxc-request/{email_or_username}/{hostname}/denial',
    status_code=201,
    responses={400: {"model": models.rest.Error}}
)
async def deny_lxc_request(
    email_or_username: str,
    serialized: models.jwt.Serialized,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin(bearer_account)

    try:
        request = serialized.deserialize_verify(models.proxmox.LXCRequest, config.links.jwt.public_key)
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
        f"""**{resource_account.username} ({resource_account.email}) request for a LXC named `{hostname}` was denied!**"""
    )

    providers.email.send(
        [resource_account.email],
        f"Linux Container '{hostname}' request denied",
        templates.email.netsoc.render(
            heading=f"Linux Container - '{hostname}' ",
            paragraph=
            f"""Hi {resource_account.username}!<br/><br/>
                We received your request for a Linux Container (LXC) named '{hostname}'<br/>
                Unfortunately we've had to deny the request for now.<br/><br/>
                Requests for LXCs are typically denied where we believe a Terms of Service violation may occur, or that a LXC may not be suitable for the reason specified<br/>
                If you have any questions, contact the SysAdmins on the UCC Netsoc Discord<br/>
            """
        ),
        "text/html"
    )
    
@router.get(
    '/lxc/{email_or_username}',
    status_code=200,
)
async def get_lxcs(
    email_or_username: str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    return providers.proxmox.read_lxcs_by_account(resource_account)

@router.delete(
    '/lxc/{email_or_username}/{hostname}',
    status_code=200,
)
async def delete_lxc(
    email_or_username: str,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    lxc = providers.proxmox.read_lxc_by_account(resource_account, hostname)
    providers.proxmox.delete_lxc(lxc)


@router.post(
    '/lxc/{email_or_username}/{hostname}/active',
    status_code=201,
)
async def mark_active_lxc(
    email_or_username: str,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    lxc = providers.proxmox.read_lxc_by_account(resource_account, hostname)
    providers.proxmox.mark_active_lxc(lxc)


@router.post(
    '/lxc/{email_or_username}/{hostname}/start',
    status_code=201,
)
async def start_lxc(
    email_or_username: str,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    lxc = providers.proxmox.read_lxc_by_account(resource_account, hostname)
    providers.proxmox.start_lxc(lxc)

@router.post(
    '/lxc/{email_or_username}/{hostname}/stop',
    status_code=200,
)
async def stop_lxc(
    email_or_username: str,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    lxc = providers.proxmox.read_lxc_by_account(resource_account, hostname)
    providers.proxmox.stop_lxc(lxc)


@router.post(
    '/lxc/{email_or_username}/{hostname}/shutdown',
    status_code=200,
)
async def shutdown_lxc(
    email_or_username: str,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    lxc = providers.proxmox.read_lxc_by_account(resource_account, hostname)
    providers.proxmox.shutdown_lxc(lxc)

ranged_port = models.proxmox.generate_ranged_port_field_args(config.proxmox.port_forward.range[0], config.proxmox.port_forward.range[1])

@router.post(
    '/lxc/{email_or_username}/{hostname}/port/{external_port}/{internal_port}',
    status_code=200,
)
async def add_port_lxc(
    email_or_username: str,
    hostname: str = Path(**models.proxmox.Hostname),
    external_port: int = Path(**ranged_port),
    internal_port: int = Path(**models.proxmox.Port),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    lxc = providers.proxmox.read_lxc_by_account(resource_account, hostname)
    providers.proxmox.add_port_lxc(lxc, external_port, internal_port)

@router.delete(
    '/lxc/{email_or_username}/{hostname}/port/{external_port}',
    status_code=200,
)
async def remove_port_lxc(
    email_or_username: str,
    hostname: str = Path(**models.proxmox.Hostname),
    external_port: int = Path(**models.proxmox.Port), # don't need to worry about them deleting non-ranged ports
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    lxc = providers.proxmox.read_lxc_by_account(resource_account, hostname)
    providers.proxmox.remove_port_lxc(lxc, external_port)

@router.post(
    '/lxc/{email_or_username}/{hostname}/vhost/{vhost}',
    status_code=200,
)
async def add_vhost_lxc(
    email_or_username: str,
    hostname: str = Path(**models.proxmox.Hostname),
    vhost: str = Path(**models.proxmox.VHost),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    lxc = providers.proxmox.read_lxc_by_account(resource_account, hostname)
    providers.proxmox.add_vhost_lxc(lxc, vhost)

@router.delete(
    '/lxc/{email_or_username}/{hostname}/vhost/{vhost}',
    status_code=200,
)
async def remove_vhost_lxc(
    email_or_username: str,
    hostname: str = Path(**models.proxmox.Hostname),
    vhost: str = Path(**models.proxmox.VHost),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    lxc = providers.proxmox.read_lxc_by_account(resource_account, hostname)
    providers.proxmox.remove_vhost_lxc(lxc, vhost)


@router.post(
    '/lxc/{email_or_username}/{hostname}/reset-root-user',
    status_code=200,
    response_model=models.rest.Info
)
async def reset_root_user_lxc(
    email_or_username: str,
    hostname: str = Path(**models.proxmox.Hostname),
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
) -> models.rest.Info:
    resource_account = providers.accounts.find_verified_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    lxc = providers.proxmox.read_lxc_by_account(resource_account, hostname)

    password, private_key = providers.proxmox.reset_root_user_lxc(lxc)

    providers.email.send(
        [resource_account.email],
        f"Linux Container '{hostname}' password reset",
        templates.email.netsoc.render(
            heading=f"Linux Container - '{hostname}' ",
            paragraph=
            f"""Hi {resource_account.username}!<br/><br/>
                We successfully reset the password and SSH identity for the root user on a Linux Container (LXC) named '{hostname}'<br/>
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

@router.get(
    '/vps-templates',
    status_code=200,
    response_model=Dict[str,models.proxmox.Template],
    responses={400: {"model": models.rest.Error}}
) 
async def get_vps_templates():
    return config.proxmox.vps.templates
    
# @router.get(
#     '/vps/{email_or_username}',
#     status_code=200,
#     response_model=List[models.proxmox.UserVM],
#     responses={400: {"model": models.rest.Error}}
# )
# async def get_user_vms(
#     email_or_username: str,
#     bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)


# @router.post(
#     '/vps-request/{email_or_username}/{hostname}',
#     status_code=201,
#     responses={400: {"model": models.rest.Error}}
# )
# async def create_vps_request(
#     email_or_username: str,
#     detail: models.proxmox.RequestDetail,
#     hostname: str = Path(**models.proxmox.Hostname),
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

#     if detail.template_id not in config.proxmox.uservm.templates:
#         raise exceptions.rest.Error(
#             400,
#             models.rest.Detail(
#                 msg=f"VPS template {detail.template_id} does not exist!"
#             )
#         )

#     try:
#         existing_vm = providers.proxmox.read_uservm_by_account(resource_account, hostname)
#         raise exceptions.resource.AlreadyExists(f"VPS {hostname} already exists!")
#     except exceptions.resource.NotFound as e:
#         pass

#     serialized = models.proxmox.VPSRequest(
#         username=resource_account.username,
#         hostname=hostname,
#         detail=detail
#     ).sign_serialize(config.links.jwt.private_key)

#     utilities.webhook.info(
# f"""**{resource_account.username} ({resource_account.email}) requested a VPS!**
# They want `{detail.template_id}` for the following reason: ```{detail.reason}```.

# To approve this request, sign in to a SysAdmin link and click the following link: `{serialized.token}`"""
#     )

#     providers.email.send(
#         [resource_account.email],
#         f"Virtual Private Server '{hostname}' requested",
#         templates.email.netsoc.render(
#             heading=f"VPS Request - '{hostname}'",
#             paragraph=
#             f"""Hi {resource_account.username}!<br/><br/>
#                 We've received your request for a Virtual Private Server named '{hostname}'<br/>
#                 We will notify you by email as soon as we have approved/denied your request<br/><br/>
#                 If you do not receive a response within 2-3 days, contact the SysAdmins on the UCC Netsoc Discord<br/>
#                 Once you make contact, they might request the information below:<br/>
#             """,
#             embeds=[
#                 { "text": serialized.token }
#             ],
#         ),
#         "text/html"
#     )

# @router.post(
#     '/uservm-request/{email_or_username}/{hostname}/approval",
#     status_code=201,
#     responses={400: {"model": models.rest.Error}}
# )
# async def approve_uservm_request(
#     email_or_username: str,
#     serialized_request: models.jwt.Serialized,
#     hostname: str = Path(**models.proxmox.Hostname),
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin(bearer_account, resource_account)


# @router.post(
#     '/uservm-request/{email_or_username}/{hostname}/denial',
#     status_code=200,
#     responses={401: {"model": models.rest.Error}}
# )
# async def deny_uservm_request(
#     email_or_username: str,
#     serialized_request: models.jwt.Serialized,
#     hostname: str = Path(**models.proxmox.Hostname),
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin(bearer_account, resource_account)


    

# @router.get(
#     '/vm-templates',
#     status_code=200,
#     response_model=Dict[str, models.proxmox.Image],
#     responses={400: {"model": models.rest.Error}}
# )
# async def get_vm_images():
#     return config.proxmox.uservm.images


# @router.get(
#     '/lxc-templates',
#     status_code=200,
#     response_model=Dict[str, models.proxmox.Image],
#     responses={400: {"model": models.rest.Error}}
# )
# async def get_vm_images():
#     return config.proxmox.uservm.images



# @router.post(
#     '/vm/{email_or_username}/{hostname}/',
#     status_code=201,
#     responses={400: {"model": models.rest.Error}}
# )
# async def request_vm(
#     email_or_username: str,
#     body: VPSRequest,
#     hostname: str = Path(**models.proxmox.Hostname),
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)



# @router.post(
#     '/vm/{email_or_username}/{hostname}',
#     status_code=201,
#     responses={400: {"model": models.rest.Error}}
# )
# async def request_vm(
#     email_or_username: str,
#     body: ReasonBody,
#     hostname: str = Path(**models.proxmox.Hostname),
#     bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

#     if body.image_id in config.proxmox.uservm.images:
#         image = config.proxmox.uservm.images[body.image_id]

#         providers.proxmox.request_uservm(
#             resource_account,
#             hostname,
#             image,
#             body.reason
#         )
#     else:
#         raise exceptions.rest.Error(
#             400,
#             models.rest.Detail(
#                 msg=f"Image {body.image_id} does not exist!"
#             )
#         )
        
# @router.post(
#     '/vm/{email_or_username}/{hostname}/approve',
#     status_code=201,
#     responses={400: {"model": models.rest.Error}}
# )
# async def approve_vm(
#     email_or_username: str,
#     hostname: str = Path(**models.proxmox.Hostname),
#     bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin(bearer_account)

#     vm = providers.proxmox.read_uservm_by_account(resource_account, hostname)

#     providers.proxmox.approve_uservm(vm)
 
# @router.post( 
#     '/vm/{email_or_username}/{hostname}/suspend',
#     status_code=201,
#     responses={400: {"model": models.rest.Error}}
# )
# async def suspend_vm(
#     email_or_username: str,
#     suspension: models.proxmox.Suspension,
#     hostname: str = Path(**models.proxmox.Hostname),
#     bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin(bearer_account)

#     vm = providers.proxmox.read_uservm_by_account(resource_account, hostname)

#     providers.proxmox.suspend_uservm(vm, suspension)

# @router.post(
#     '/vm/{email_or_username}/{hostname}/flash-image',
#     status_code=201,
#     responses={400: {"model": models.rest.Error}}
# )
# async def flash_vm_image(
#     email_or_username: str,
#     hostname: str = Path(**models.proxmox.Hostname),
#     bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

#     vm = providers.proxmox.read_uservm_by_account(resource_account, hostname)

#     providers.proxmox.flash_uservm_image(vm)

# @router.delete(
#     '/vm/{email_or_username}/{hostname}',
#     status_code=200,
#     responses={400: {"model": models.rest.Error}}
# )
# async def delete_vm(
#     email_or_username: str,
#     hostname: str = Path(**models.proxmox.Hostname),
#     bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

#     vm = providers.proxmox.read_uservm_by_account(resource_account, hostname)

#     providers.proxmox.delete_uservm(vm)


# @router.post(
#     '/vm/{email_or_username}/{hostname}/mark-active',
#     status_code=200,
#     responses={400: {"model": models.rest.Error}}
# )
# async def mark_active_vm(
#     email_or_username: str,
#     hostname: str = Path(**models.proxmox.Hostname),
#     bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

#     vm = providers.proxmox.read_uservm_by_account(resource_account, hostname)

#     providers.proxmox.mark_active_uservm(vm)

# @router.post(
#     '/vm/{email_or_username}/{hostname}/start',
#     status_code=200,
#     responses={400: {"model": models.rest.Error}}
# )
# async def start_vm(
#     email_or_username: str,
#     hostname: str = Path(**models.proxmox.Hostname),
#     bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

#     vm = providers.proxmox.read_uservm_by_account(resource_account, hostname)

#     providers.proxmox.start_uservm(vm)


# @router.post(
#     '/vm/{email_or_username}/{hostname}/stop',
#     status_code=200,
#     responses={400: {"model": models.rest.Error}}
# )
# async def stop_vm(
#     email_or_username: str,
#     hostname: str = Path(**models.proxmox.Hostname),
#     bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

#     vm = providers.proxmox.read_uservm_by_account(resource_account, hostname)

#     providers.proxmox.stop_uservm(vm)

# @router.post(
#     '/vm/{email_or_username}/{hostname}/shutdown',
#     status_code=200,
#     responses={400: {"model": models.rest.Error}}
# )
# async def shutdown_vm(
#     email_or_username: str,
#     hostname: str = Path(**models.proxmox.Hostname),
#     bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

#     vm = providers.proxmox.read_uservm_by_account(resource_account, hostname)

#     providers.proxmox.shutdown_uservm(vm)



# @router.get(
#     '/vm/{email_or_username}/{hostname}/domains',
#     status_code=200,
#     responses={400: {"model": models.rest.Error}}
# )
# async def get_domains_vm(
#     email_or_username: str,
#     hostname: str = Path(**models.proxmox.Hostname),
#     bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

#     vm = providers.proxmox.read_uservm_by_account(resource_account, hostname)

#     providers.proxmox.shutdown_uservm(vm)



# @router.post(
#     '/vm/{email_or_username}/{hostname}/domains/{domain}',
#     status_code=201,
#     responses={400: {"model": models.rest.Error}}
# )
# async def add_domain_vm(
#     email_or_username: str,
#     hostname: str = Path(**models.proxmox.Hostname),
#     bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

#     vm = providers.proxmox.read_uservm_by_account(resource_account, hostname)

#     providers.proxmox.shutdown_uservm(vm)


# @router.delete(
#     '/vm/{email_or_username}/{hostname}/domains/{domain}',
#     status_code=200,
#     responses={400: {"model": models.rest.Error}}
# )
# async def delete_domain_vm(
#     email_or_username: str,
#     hostname: str = Path(**models.proxmox.Hostname),
#     bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

#     vm = providers.proxmox.read_uservm_by_account(resource_account, hostname)

#     providers.proxmox.shutdown_uservm(vm)



# @router.get(
#     '/vm/{email_or_username}/{hostname}/ports',
#     status_code=200,
#     responses={400: {"model": models.rest.Error}}
# )
# async def get_ports_vm(
#     email_or_username: str,
#     hostname: str = Path(**models.proxmox.Hostname),
#     bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

#     vm = providers.proxmox.read_uservm_by_account(resource_account, hostname)

#     providers.proxmox.shutdown_uservm(vm)



# @router.post(
#     '/vm/{email_or_username}/{hostname}/ports/{external_port}/{internal_port}',
#     status_code=201,
#     responses={400: {"model": models.rest.Error}}
# )
# async def add_port_vm(
#     email_or_username: str,
#     hostname: str = Path(**models.proxmox.Hostname),
#     bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

#     vm = providers.proxmox.read_uservm_by_account(resource_account, hostname)

#     providers.proxmox.shutdown_uservm(vm)


# @router.delete(
#     '/vm/{email_or_username}/{hostname}/ports/{external_port}/{internal_port}',
#     status_code=200,
#     responses={400: {"model": models.rest.Error}}
# )
# async def delete_port_vm(
#     email_or_username: str,
#     hostname: str = Path(**models.proxmox.Hostname),
#     bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
# ):
#     resource_account = providers.accounts.find_verified_account(email_or_username)
#     utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

#     vm = providers.proxmox.read_uservm_by_account(resource_account, hostname)

#     providers.proxmox.shutdown_uservm(vm)
