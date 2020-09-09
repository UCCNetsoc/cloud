import os
import errno
from pathlib import Path
from typing import Dict
import structlog as logging
import stat
import python_freeipa as freeipa
import requests

from pydantic import EmailStr
from v1 import models, exceptions
from v1.config import config

logger = logging.getLogger(__name__)

import warnings

# TODO(ocanty) - write context manager for _client that toggles this
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class FreeIPA:    
    def __init__(self):
        logger.info("FreeIPA provider created")
        logger.info("Ensuring groups setup in FreeIPA")
        for group in models.group.groups:
            if not self.group_exists(group.group_name):
                logger.info(f"Group {group.group_name} not found, adding", group=group)
                self._client.group_add(
                    a_cn = group.group_name,
                    o_description = group.description,
                    o_gidnumber = group.gid
                )

    _client_instance: freeipa.ClientMeta = None

    @property
    def _client(self):
        if self._client_instance is None:
            try:
                logger.info("FreeIPA client creating...", server=config.accounts.freeipa.server)
                self._client_instance = freeipa.ClientMeta(
                    config.accounts.freeipa.server,
                    dns_discovery=True,
                    verify_ssl=False
                )
                
                logger.info("FreeIPA client logging in", username=config.accounts.freeipa.username)
                self._client_instance.login(
                    config.accounts.freeipa.username,
                    config.accounts.freeipa.password
                )
                logger.info("FreeIPA provider logged in")
            except Exception as e:
                logger.error(f"FreeIPA provider unavailable: {e}")
                raise exceptions.provider.Unavailable(f"Couldn't connect to FreeIPA server: {e}")

        try:
            # The FreeIPA session can expire every 15 minutes so we need to test if we're still logged in
            self._client_instance.ping()
        except freeipa.exceptions.Unauthorized as e:
            logger.info("FreeIPA provider session expired")

            try:
                logger.info("FreeIPA client logging in", username=config.accounts.freeipa.username)
                self._client_instance.login(
                    config.accounts.freeipa.username,
                    config.accounts.freeipa.password
                )
                logger.info("FreeIPA provider logged in")
            except Exception as e:
                logger.error(f"FreeIPA provider unavailable: {e}")
                raise exceptions.provider.Unavailable(f"Couldn't connect to FreeIPA server: {e}")

        return self._client_instance

    def change_password(
        self,
        account: models.account.Account, 
        password: models.password.Password
    ):
        find = self._client.user_find(
            o_uid=account.username
        )

        find2 = self._client.stageuser_find(
            o_uid=account.username
        )

        if find['count'] > 0:
            self._client.user_mod(a_uid=find['result'][0]['uid'][0], o_userpassword=password)

            # FreeIPA has a security feature that invalidates a password as soon as it's changed by an administrator
            # i.e as soon as they log in with the password that has been set, SSSD or the web UI will prompt them to immediately change it
            # (so the administrator doesn't know their password)
            # This can be worked around that by simulating the Web UI action here (without the users knowledge)
            # await fetch("https://ipa.netsoc.dev/ipa/session/change_password", {
            #     "credentials": "omit",
            #     "headers": {
            #         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:79.0) Gecko/20100101 Firefox/79.0",
            #         "Accept": "text/html, */*; q=0.01",
            #         "Accept-Language": "en-US,en;q=0.5",
            #         "Content-Type": "application/x-www-form-urlencoded",
            #         "X-Requested-With": "XMLHttpRequest"
            #     },
            #     "referrer": "https://ipa.netsoc.dev/ipa/ui/",
            #     "body": "user=ayy123&old_password=ayylmao123&new_password=ayylmao123",
            #     "method": "POST",
            #     "mode": "cors"
            # });
            #
            # Thankfully, python-freeipa also has a feature that does this
            self._client.change_password(account.username, password, password)

        elif find2['count'] > 0:
            self._client.stageuser_mod(a_uid=find2['result'][0]['uid'][0], o_userpassword=password)

            self._client.change_password(account.username, password, password)
        else:
            raise exceptions.resource.NotFound("could not find user account")

    def find_account(
        self,
        email_or_username: str
    ) -> models.account.Account:
        account = None 

        if self.username_exists(email_or_username):
            account = self.read_account_by_username(email_or_username)
        elif self.email_exists(email_or_username):
            account = self.read_account_by_email(email_or_username)

        if account is None:
            raise exceptions.resource.NotFound()
        
        return account

    def find_verified_account(
        self,
        email_or_username: str
    ) -> models.account.Account:
        account = self.find_account(email_or_username)

        if account.verified is False:
            raise exceptions.resource.NotFound("An account was found but it is not verified")
        
        return account

    def username_exists(
        self,
        username: models.account.Username
    ) -> bool:
        res = self._client.user_find(o_uid=username)
        res2 = self._client.stageuser_find(o_uid=username)
        return (res['count'] > 0 or res2['count'] > 0)

    def email_exists(
        self,
        email: EmailStr
    ) -> bool:
        res = self._client.user_find(o_mail=email)
        res2 = self._client.stageuser_find(o_mail=email)
        return (res['count'] > 0 or res2['count'] > 0)

    def group_exists(
        self,
        group_name: models.group.GroupName
    ):
        res = self._client.group_find(o_cn=group_name)
        return (res['count'] > 0)


    def _populate_accounts_from_user_find(self, find) -> Dict[str, models.account.Account]:
        if find['count'] == 0:
            return {}

        accounts = {}

        for i in range(find['count']):
            groups = {}
            
            for group in find['result'][i]['memberof_group']:
                group_find = self._client.group_find(o_cn=group)

                if group_find['count'] != 0 and 'posixgroup' in group_find['result'][0]['objectclass']:
                    description = None
                    if 'description' in group_find['result'][0]:
                        description = group_find['result'][0]['description'][0]

                    group_name = group_find['result'][0]['cn'][0]
                    groups[group_name] = models.group.Group(
                        group_name = group_find['result'][0]['cn'][0],
                        description = description,
                        gid = group_find['result'][0]['gidnumber'][0]
                    )

            username = find['result'][i]['uid'][0]
            accounts[username] = models.account.Account(
                username=find['result'][i]['uid'][0],
                email=find['result'][i]['mail'][0] if 'mail' in find['result'][i] else None,
                uid=find['result'][i]['uidnumber'][0],
                groups=groups,
                home_dir=find['result'][i]['homedirectory'][0],
                verified=True
            )

        return accounts


    def _populate_accounts_from_stageuser_find(self, find) -> Dict[str, models.account.Account]:
        if find['count'] == 0:
            return {}

        accounts = {}
        for i in range(find['count']):
            username = find['result'][0]['uid'][0]
            accounts[username] = models.account.Account(
                username=find['result'][0]['uid'][0],
                email=find['result'][0]['mail'][0],
                groups={},
                home_dir=None,
                verified=False  
            )

        return accounts

    def read_account_by_username(
        self,
        username : models.account.Username
    ) -> models.account.Account:
        find = self._client.user_find(
            o_uid=username
        )

        find2 = self._client.stageuser_find(
            o_uid=username
        )

        if find['count'] > 0:
            return self._populate_accounts_from_user_find(find)[username]
        elif find2['count'] > 0:
            return self._populate_accounts_from_stageuser_find(find2)[username]
        else:
            raise exceptions.resource.NotFound()

    def read_account_by_email(
        self,
        email : EmailStr
    ) -> models.account.Account:
        find = self._client.user_find(
            o_mail=email
        )

        find2 = self._client.stageuser_find(
            o_mail=email
        )

        if find['count'] > 0:
            return list(self._populate_accounts_from_user_find(find).items())[0][1]
        elif find2['count'] > 0:
            return list(self._populate_accounts_from_stageuser_find(find2).items())[0][1]
        else:
            raise exceptions.resource.NotFound()


    def read_accounts_all(
        self
    ) -> Dict[str, models.account.Account]:
        find = self._client.user_find()
        find2 = self._client.stageuser_find()

        accounts = self._populate_accounts_from_user_find(find)
        staged_accounts = self._populate_accounts_from_stageuser_find(find2)

        return {**staged_accounts, **accounts}

    def create_account(
        self,
        sign_up
    ):
        if self.username_exists(sign_up.username):
            raise exceptions.resource.AlreadyExists("account already exists with this username")

        if self.email_exists(sign_up.username):
            raise exceptions.resource.AlreadyExists("account already exists with this email")

        if self.group_exists(sign_up.username):
            raise exceptions.resource.AlreadyExists("group already exists with this username")

        home_dir = Path(f"{config.accounts.home_dirs.resolve()}/{sign_up.username}")

        # if home_dir.is_symlink():
        #     raise exceptions.resource.AlreadyExists("home directory already exists as a symlink")
        
        # if home_dir.exists():
        #     raise exceptions.resource.AlreadyExists("home directory already exists")

        add = self._client.stageuser_add(
            a_uid=sign_up.username,
            o_userpassword=sign_up.password,
            o_loginshell="/bin/bash",

            # first name
            o_givenname=sign_up.username,

            # last name
            o_sn="-",

            # full names
            o_cn=sign_up.username,
            o_displayname=sign_up.username,
            o_homedirectory=str(home_dir),
            o_mail=sign_up.email
        )
        
    def verify_account(
        self,
        account: models.account.Account
    ):
        """
        Activates an account
        """
        # First lookup account to see if it's a stage account
        find = self._client.stageuser_find(
            o_uid=account.username
        )

        if find['count'] == 0:
            raise exceptions.resource.NotFound(f"could not find unactivated account: {account.username}")

        # Activate the user
        self._client.stageuser_activate(account.username)

        # Add the user we just activated to account group
        for group in [models.group.NetsocAccount]:
            try:
                self._client.group_add_member(
                    a_cn=group.group_name,
                    o_user=account.username
                )
            except freeipa.exceptions.FreeIPAError as e:
                raise exceptions.provider.Failed(f"error adding newly activated user to group: {e}")

        account = self.read_account_by_username(account.username)

    def read_gdpr_data(
        self,
        account: models.account.Account
    ) -> dict:
        find = self._client.user_find(
            o_mail=account.email,
            o_all=True
        )

        find2 = self._client.stageuser_find(
            o_mail=account.email,
            o_all=True
        )

        if find['count'] > 0:
            return find['result'][0]
        elif find2['count'] > 0:
            return find2['result'][0]