from fastapi import APIRouter, Path, Depends
from typing import Dict

from v1 import providers, templates, models, exceptions, utilities
from v1.config import config

router = APIRouter()

@router.get(
    '/available',
    status_code=200,
    response_model=Dict[str,models.mentorship.Mentorship]
)
async def get_mentorships():
    return config.mentorships.available
        
@router.post(
    '/{name}/enroll',
    status_code=201,
    response_model=models.rest.Info
)
async def enroll_in_mentorship(
    name: str,
    enrollment: models.mentorship.Enrollment,
    account: models.account.Account = Depends(utilities.auth.get_bearer_account)
):
    if name in config.mentorships.available:
        mentorship = config.mentorships.available[name]

        utilities.webhook.form_filled(
            f"**{account.username} ({account.email})** enrolled in **{mentorship.title} by {mentorship.teacher}** because: ```{enrollment.reason}```"
        )

        providers.email.send(
            [account.email],
            f'Mentorship Enrollment - {mentorship.title} by {mentorship.teacher}',
            templates.email.netsoc.render(
                heading="Mentorship Enrollment",
                paragraph=f"""Hi {account.username}!<br/><br/>You've successfully registered interest in:<br/><b>{mentorship.title} by {mentorship.teacher}</b>!<br/><br/>
                    If you are accepted, you will receive an email close to the beginning of the mentorship with further details<br/>"""
            ),
            "text/html"
        )

        return models.rest.Info(
            detail=models.rest.Detail(
                msg=f"Successfully registered interest in {mentorship.title}, a email will be sent to the email address associated with this account near the beginning of the mentorship"
            )
        )
    else:
        raise exceptions.resource.NotFound(f"mentorship {name} does not exist")



