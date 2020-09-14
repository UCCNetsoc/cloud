from fastapi import APIRouter, HTTPException, Depends
import time

from v1 import models, exceptions, templates, providers, utilities
from v1.config import config

import structlog as logging

logger = logging.getLogger(__name__)
logger.info(f"", providers=providers)

router = APIRouter()

@router.get(
    '/',
    status_code=200,
    response_model=models.account.Account
)
async def get_bearer_account(
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    return bearer_account

# Endpoint that sends verification email
@router.post(
    '/{email_or_username}/verification-email',
    status_code=201,
    response_model=models.rest.Info,
)
async def send_verification_email(email_or_username : str, body : models.account.EmailVerification):
    if not utilities.hcaptcha.verify_hcaptcha(body.captcha):
        return models.rest.Error(
            detail=models.rest.Detail(
                msg=f"Invalid captcha"
            )
        )

    resource_account = providers.accounts.find_account(email_or_username)

    if resource_account.verified:
        providers.email.send(
            [resource_account.email],
            'Welcome to Netsoc Admin!',
            templates.email.netsoc.render(
                heading="Welcome to Netsoc Admin!",
                paragraph=f"""Hi {resource_account.username}!<br/><br/>It seems like you tried to create/verify an account but there already is a verified account under this email address!<br/>
                    If you have forgotten your password and want to reset it, you can click the button below:""",
                buttons=[
                    { "text": "Reset Password", "link": f"{config.links.base_url}/account/{resource_account.username}/password-reset"}
                ],
            ),
            "text/html"
        )
    else:
        serialized = models.sign_up.Verification(
            iat=time.time(),
            exp=time.time() + 3600,
            username=resource_account.username
        ).sign_serialize(config.links.jwt.private_key)

        providers.email.send(
            [resource_account.email],
            'Welcome to Netsoc Admin!',
            templates.email.netsoc.render(
                heading="Welcome to Netsoc Admin!",
                paragraph=f"""Hi {resource_account.username}!<br/><br/>You're just about ready to get started using UCC Netsoc services!<br/>
                    Click the button below to verify your account""",
                buttons=[
                    { "text": "Verify Account", "link": f"{config.links.base_url}/account/{resource_account.username}/verification/{serialized.token}"}
                ],
            ),
            "text/html"
        )

        utilities.webhook.info(f"**Verification email sent** - {resource_account.username} ({resource_account.email})")

    return models.rest.Info(
        detail=models.rest.Detail(
            msg=f"A verification email has been sent to the email address associated with the account"
        )
    )

# When they click the sign-up link in their email, the UI should send us the sign in code
@router.post(
    '/{email_or_username}/verification',
    status_code=201,
    response_model=models.rest.Info,
    responses={400: {"model": models.rest.Error}, 500: {"model": models.rest.Error}}
)
async def verification(
    email_or_username: str,
    serialized: models.jwt.Serialized
):
    resource_account = providers.accounts.find_account(email_or_username)

    if resource_account.verified == False:
        verification = serialized.deserialize_verify(models.sign_up.Verification, config.links.jwt.public_key)

        if resource_account.username == verification.username:
            providers.accounts.verify_account(resource_account)

            utilities.webhook.info(f"**Account verified** - {resource_account.username} ({resource_account.email})")
            
            return models.rest.Info(
                detail=models.rest.Detail(msg=f"The account has been verified. It should now be possible to log in")
            )
        else:
            raise exceptions.rest.Error(status_code=400, detail=models.rest.Detail(
                msg="This verification token is for a different user"
            ))

    raise exceptions.rest.Error(status_code=400, detail=models.rest.Detail(
        msg="The account has already been verified",
    ))

@router.post(
    '/{email_or_username}/password-reset-email',
    status_code=201,
    response_model=models.rest.Info,
    responses={400: {"model": models.rest.Error}}
)
async def send_password_reset_email(
    email_or_username : str,
    body : models.account.EmailVerification
):
    if not utilities.hcaptcha.verify_hcaptcha(body.captcha):
        return models.rest.Error(
            detail=models.rest.Detail(
                msg=f"Invalid captcha"
            )
        )
    resource_account = providers.accounts.find_account(email_or_username)

    if resource_account.verified:
        serialized = models.password.Reset(
            iat=time.time(),
            exp=time.time() + 3600,
            username=resource_account.username
        ).sign_serialize(config.links.jwt.private_key)

        providers.email.send(
            [resource_account.email],
            'Password Reset',
            templates.email.netsoc.render(
                heading="Password Reset",
                paragraph=f"""Hi {resource_account.username}!<br/><br/>Click the button below to reset your password.""",
                buttons=[
                    { "text": "Reset Password", "link": f"{config.links.base_url}/account/{resource_account.username}/password/{serialized.token}"}
                ],
            ),
            "text/html"
        )

        utilities.webhook.info(f"**Requested password reset** - {resource_account.username} ({resource_account.email})")

    else:
        providers.email.send(
            [resource_account.email],
            'Password Reset',
            templates.email.netsoc.render(
                heading="Password Reset",
                paragraph=f"""Hi {resource_account.username}!<br/><br/>It seems like you tried to reset a password for an unverified account!<br/>
                    You can resend the account verification by clicking the button below, you will then be able to reset the password""",
                buttons=[
                    { "text": "Resend Verification", "link": f"{config.links.base_url}/account/{resource_account.username}/verification-email"}
                ],
            ),
            "text/html"
        )

    return models.rest.Info(
        detail=models.rest.Detail(
            msg=f"A password reset link has been sent to the email associated with the account"
        )
    )

@router.post(
    '/{email_or_username}/password',
    status_code=201,
    response_model=models.rest.Info,
    responses={400: {"model": models.rest.Error}, 500: {"model": models.rest.Error}}
)
async def set_password(
    email_or_username : str,
    new: models.password.New
):
    resource_account = providers.accounts.find_account(email_or_username)
    reset = new.reset.deserialize_verify(models.password.Reset, config.links.jwt.public_key)

    if resource_account.username == reset.username:
        providers.accounts.change_password(resource_account, new.password)

        utilities.webhook.info(f"**Password reset** - {resource_account.username} ({resource_account.email})")
    else:
        raise exceptions.rest.Error(status_code=400, detail=models.rest.Detail(
            msg="This password reset token is for a different user"
        ))

    return models.rest.Info(
        detail=models.rest.Detail(
            msg="Password reset successfully"
        )
    )

@router.get(
    '/{email_or_username}/gdpr-data',
    status_code=200
)
async def get_gpdr_data(
    email_or_username : str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    utilities.webhook.info(f"**Requested GDPR data** - {resource_account.username} ({resource_account.email})")

    return providers.accounts.read_gdpr_data(resource_account)

    
@router.get(
    '/{email_or_username}/home-directory',
    status_code=200,
    response_model=models.rest.Info
)
async def get_home_directory(
    email_or_username : str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)

    if resource_account.verified is False:
        raise exceptions.rest.Error(
            status_code=400,
            detail=models.rest.Detail(
                msg="Account is not verified, cannot have a home directory yet"
            )
        )

    if resource_account.home_dir.exists():
        return models.rest.Info(
            detail=models.rest.Detail(
                msg="Home directory exists"
            )
        )
    else:
        raise exceptions.rest.Error(
            status_code=404,
            detail=models.rest.Detail(
                msg="Home directory doesn't exist"
            )
        )

@router.post(
    '/{email_or_username}/home-directory',
    status_code=201
)
async def create_home_directory(
    email_or_username : str,
    bearer_account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    resource_account = providers.accounts.find_account(email_or_username)
    utilities.auth.ensure_sysadmin_or_acting_on_self(bearer_account, resource_account)
    
    if resource_account.verified is False:
        raise exceptions.rest.Error(
            status_code=400,
            detail=models.rest.Detail(
                msg="Account is not verified, cannot have a home directory yet"
            )
        )

    providers.mkhomedir.create(resource_account)
    utilities.webhook.info(f"**Home directory created** - {resource_account.username} ({resource_account.email})")

    return models.rest.Info(
        detail=models.rest.Detail(
            msg="Home directory created"
        )
    )

