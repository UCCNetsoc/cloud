import logging
from typing import List

from v1 import exceptions
from v1.config import config

import sendgrid
from sendgrid.helpers import mail

import structlog as logging

class SendGrid:
    logger = logging.getLogger(f"{__name__}.sendgrid")

    _sg : sendgrid.SendGridAPIClient

    def __init__(self):
        self.logger.info("sendgrid email provider created")

        self._sg = sendgrid.SendGridAPIClient(api_key=config.email.sendgrid.key)

    def send(self, to_email: List[str], subject: str, content: str, mime_type: str = 'text/plain'):
        try:
            from_email = mail.From(email=config.email.from_address, name=config.email.from_name)
            to_email   = mail.To(to_email)

            m = mail.Mail(from_email, to_email, subject, mail.Content(mime_type, content))
            m.reply_to = mail.ReplyTo(config.email.reply_to_address)

            res = self._sg.client.mail.send.post(request_body=m.get())   
            self.logger.info(f"sendgrid email sent", res=res)
        except Exception as e:
            print(e)
            raise exceptions.provider.Failed(f"Could not send email: {e}")
        

class Debug:
    logger = logging.getLogger(f"{__name__}.debug")

    def __init__(self):
        self.logger.info("debug email provider created")

    def send(self, to_email: List[str], subject: str, content: str, mime_type: str = 'text/plain'):
        self.logger.info("sending email: ", to_email=to_email, subject=subject, content=content, mime_type=mime_type)