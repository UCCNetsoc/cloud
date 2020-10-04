
from . import models, providers
from .config import config

import structlog as logging
import json

import requests
import requests.auth

logger = logging.getLogger(__name__)

from prometheus_client import Gauge

w = Gauge('netsocadmin_webserver_configurator_num_websites', 'Number of Netsoc Admin websites')
wv = Gauge('netsocadmin_webserver_configurator_num_valid_websites', 'Number of valid Netsoc Admin websites')
wiv = Gauge('netsocadmin_webserver_configurator_num_invalid_websites', 'Number of invalid Netsoc Admin websites')
lca = Gauge('netsocadmin_webserver_configurator_last_attempted_config_time', 'Unixtime of the last time we attempted to configure the Netsoc Admin user webservers')
lsc = Gauge('netsocadmin_webserver_configurator_last_successful_config_time', 'Unixtime of the last time we successfully configured the Netsoc Admin user webservers')

# Currently sets up vhosts for Nginx Unit
# This could be adapted to set this up for stuff like Nginx or Apache if we wanted in the future
def configure():
    lca.set_to_current_time()

    logger.info("webserver configurator started")

    c = {
        "listeners": {
            "*:8080": {
                "pass": "routes"
            }
        },
        "applications": {},
        "routes": []
    }
    
    accounts = providers.accounts.read_accounts_all()

    num_websites, num_valid, num_invalid = 0, 0, 0

    for username, account in accounts.items():
        logger.info("scanning ", account=account)
        if not account.verified:
            continue

        if not models.group.NetsocAccount.group_name in account.groups:
            continue

        try:
            websites = providers.websites.read_all_by_account(account).items()
        except Exception as e:
            logger.warning(f"Ignoring websites for account due to exception when reading", e=e, exc_info=True, account=account)
            continue

        for name, website in websites:
            num_websites += 1

            if not website.valid:
                num_invalid += 1
                continue
            
            num_valid += 1
                
            # Only support PHP and static content for now and assume they're using Wordpress
            website_id = f"{website.username}{str(website.root).replace('/','-')}"
            if len(website.config.hosts):
                def _get_targets():
                    if website.root.joinpath("index.php").exists():
                        return {
                            "index": { 
                                "root": "/",
                                "script": "index.php"
                            },
                            "direct": {
                                "root": "/"
                            }
                        }
                    else:
                        return {
                            "direct": {
                                "root": "/"
                            }
                        }

                c["applications"][website_id] = {
                    "type": "php",
                    "targets": _get_targets(),
                    "isolation": {
                        "namespaces": {
                            "cgroup": True,
                            "credential": True,
                            "mount": True,
                            "network": True,
                            "pid": True,
                            "uname": True
                        },
                        "uidmap": [{
                            "host": website.uid,
                            "container": 0,
                            "size": 1
                        }],
                        "gidmap": [{
                            "host": website.uid,
                            "container": 0,
                            "size":  1
                        }],
                        "rootfs": f"{website.root}",
                    },
                    "user": f"root",
                    "group": f"root"
                }

                if 'direct' in _get_targets():
                    # Match direct PHP
                    c["routes"].append({
                        "match": {
                            "host": list(website.config.hosts),
                            "uri": [
                                "*.php", "*.php/*", "/wp-admin/"
                            ]
                        },
                        "action": {
                            "pass": f"applications/{website_id}/direct"
                        }
                    })
                
                if 'index' in _get_targets():
                    # Match static files or else send the request to the index.php (for slugs)
                    c["routes"].append({ 
                        "match": {
                            "host": list(website.config.hosts)
                        },
                        "action": {
                            "share": f"{website.root}",
                            "fallback": {
                                "pass": f"applications/{website_id}/index"
                            }
                        }
                    })
                else:
                    c["routes"].append({ 
                        "match": {
                            "host": list(website.config.hosts)
                        },
                        "action": {
                            "share": f"{website.root}"
                        }
                    })
    
    w.set(num_websites)
    wv.set(num_valid)
    wiv.set(num_invalid)

    logger.info("config built for unit", **c)
    logger.info("configuring webserver targets now")
    for target in config.webserver_configurator.unit.targets:
        logger.info("configuring target", target=target)
        try:
            res = requests.put(
                "http://"+target+"/config",
                data=json.dumps(c),
                headers={
                    "Content-Type": "application/json",
                },
                auth=requests.auth.HTTPBasicAuth(
                    config.webserver_configurator.unit.basic_auth.username,
                    config.webserver_configurator.unit.basic_auth.password
                ),
                timeout=2
            )

            if res.status_code != requests.codes.ok:
                logger.error(f"could not update unit config", res=res, reason=res.content)
            else:
                lsc.set_to_current_time()
                logger.info("successfully updated unit config")
        except Exception as e:
            logger.error(f"could not update nginx unit config: {e}")
