
from v1.config import config

import json
import requests
import structlog as logging

logger = logging.getLogger(__name__)

def form_filled(content):
    return execute(config.webhooks.form_filled, content)

def info(content):
    return execute(config.webhooks.info, content)

def execute(url, content):
    try:
        discord(url, content)
    except Exception as e:
        logger.error("couldn't push webhook due to exception ${e}", url=url, content=content)


def discord(url, content):
    res = requests.post(url, data=json.dumps({
        "username": "Netsoc Admin",
        "content": f"{content}",
        "avatar_url": "https://raw.githubusercontent.com/UCCNetsoc/wiki/master/assets/logo-icon.png"
        }).encode("utf8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"
        }
    )

    logger.info("discord webhook posted", res=res, status_code=res.status_code)
