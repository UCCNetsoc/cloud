
import os
import structlog as logging

from v1 import providers, utilities, config

logger = logging.getLogger(__name__)

from prometheus_client import Gauge

a = Gauge('netsocadmin_homedir_consistency_num_accounts', 'Number of Netsoc Admin accounts')
av = Gauge('netsocadmin_homedir_consistency_num_verified_accounts', 'Number of verified Netsoc Admin accounts')
auv = Gauge('netsocadmin_homedir_consistency_num_unverified_accounts', 'Number of unverified Netsoc Admin accounts')
lca = Gauge('netsocadmin_homedir_consistency_last_attempted_config_time', 'Unixtime of the last time we attempted to ensure home dir permissions consistency')
lsc = Gauge('netsocadmin_homedir_consistency_last_successful_config_time', 'Unixtime of the last time we successfully ensured home dir permissions consistency')

def ensure():
    logger.info("home directory consistency scan started")
    lca.set_to_current_time()

    accounts = providers.accounts.read_accounts_all()
    a.set(len(accounts.items()))

    num_verified, num_unverified = 0, 0

    for username, account in accounts.items():
        if account.verified == False:
            num_unverified += 1
            continue
        
        num_verified += 1

        try:
            home_stat = account.home_dir.stat()
        except Exception as e:
            logger.error(f"could not stat {username}'s home directory, does it exist? (might not have been created by their UI yet)", account=account, e=e, exc_info=True)
            continue

        if home_stat.st_uid != account.uid:
            logger.error(
                f"{username}'s home directory uid ({home_stat.st_uid}) does not match it's account uid ({account.uid}), cannot continue scanning due to security risk!",
                stat=home_stat,
                account=account
            )
            continue

        if home_stat.st_gid != account.uid:
            logger.error(
                f"{username}'s home directory gid ({home_stat.st_gid}) does not match it's account uid ({account.ugid}), cannot continue scanning due to security risk!",
                stat=home_stat,
                account=account
            )
            continue

        if oct(home_stat.st_mode)[4:] != "771":
            try:
                os.chmod(account.home_dir, 0o771)
                logger.info(
                    f"{username}'s home directory permissions ({oct(home_stat.st_mode)[4:]}) were not set correctly, set them to 771",
                    account=account
                )
            except Exception as e:
                logger.error(f"could not update {username}'s home directory to 771", account=account, e=e, exc_info=True)
                continue

    av.set(num_verified)
    av.set(num_unverified)

    lsc.set_to_current_time()
    logger.info("home directory consistency scan done")