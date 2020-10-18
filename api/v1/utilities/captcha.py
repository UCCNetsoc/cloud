import requests
import structlog as logging

logger = logging.getLogger(__name__)

from ..config import config

def verify_captcha(token: str) -> bool:
    if config.captcha.enabled == False:
        return True

    try:
        response = requests.post(
            config.captcha.hcaptcha.url,
            {'response': token, 'secret': config.captcha.hcaptcha.secret}
        )
        response.raise_for_status()
        data = response.json()
        return data["success"]
    except requests.exceptions.RequestException as e:
        logger.error("could not test captcha", e=e, exc_info=True)
        return False
