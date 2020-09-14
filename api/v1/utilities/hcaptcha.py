import requests
from ..config import config

def verify_hcaptcha(token: str) -> bool:
    if not config.production and not config.hcaptcha.secret:
        return True
    try:
        response = requests.post(config.hcaptcha.url, {'response': token, 'secret': config.hcaptcha.secret})
        data = response.json()
        return data["success"]
    except requests.exceptions.RequestException as e:
        print(e)
        return False
