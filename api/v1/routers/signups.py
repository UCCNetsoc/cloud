import time
import traceback

from fastapi import APIRouter, HTTPException, Depends, Path
from starlette.responses import JSONResponse

from v1 import providers, templates, models, exceptions, utilities
from v1.config import config

router = APIRouter()


def handle_sign_up(
    sign_up: models.sign_up.SignUp,
):
    if providers.accounts.email_exists(sign_up.email):
        # We lie to prevent leaking student numbers/email addresses
        return models.rest.Info(
            detail=models.rest.Detail(
                msg=f"Account created"
            )
        )


    if providers.accounts.username_exists(sign_up.username):
        raise exceptions.rest.Error(status_code=409, detail=models.rest.Detail(
                msg="Username unavailable",
                loc=["username"]
            )
        )

    if providers.accounts.group_exists(sign_up.username):
        raise exceptions.rest.Error(status_code=409, detail=models.rest.Detail(
                msg="Username unavailable",
                loc=["username"]
            )
        )

    if sign_up.username in config.accounts.username_blacklist:
        raise exceptions.rest.Error(status_code=409, detail=models.rest.Detail(
                msg="Username unavailable",
                loc=["username"]
            )
        )

    providers.accounts.create_account(sign_up)
    utilities.webhook.info(f"**Account created** - {sign_up.username} ({sign_up.email})")

    return models.rest.Info(
        detail=models.rest.Detail(
            msg=f"Account created"
        )
    )


@router.post(
    '/ucc-student',
    status_code=201,
    response_model=models.rest.Info,
    responses={409: {"model": models.rest.Error}, 500: {"model": models.rest.Error}}
)
async def sign_up_UCC_student(
    sign_up    : models.sign_up.UCCStudent
):  
    return handle_sign_up(sign_up)

# @router.post(
#     '/ucc-staff',
#     status_code=201,
#     response_model=models.rest.Info,
#     responses={409: {"model": models.rest.Error}}
# )
# async def sign_up_UCC_staff(
#     sign_up    : models.sign_up.UCCStaff
# ):  
#     return handle_sign_up(sign_up)

# @router.post(
#     '/ucc-society',
#     status_code=201,
#     response_model=models.rest.Info,
#     responses={409: {"model": models.rest.Error}}
# )
# async def sign_up_UCC_society(
#     sign_up    : models.sign_up.UCCSociety
# ):  
#     return handle_sign_up(sign_up)