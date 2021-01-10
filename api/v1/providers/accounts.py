import os
import errno
from pathlib import Path
from typing import Dict
import structlog as logging
import stat
import python_freeipa as freeipa
import requests
import random
import time

from pydantic import EmailStr
from v1 import models, exceptions
from v1.config import config

logger = logging.getLogger(__name__)

import warnings

# TODO(ocanty) - write context manager for _client that toggles this
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class FreeIPASession(object):
    """
    Context manager class that keep-alives a session
    """
    _client: freeipa.ClientMeta

    def __init__(self, client):
        self._client = client

    def __enter__(self):
        self.t = time.time()
        self.nonce = random.randint(0,9999999)
        logger.info(f"freeipa session opened: {self.nonce}")
        try:
            # The FreeIPA session can expire every 15 minutes so we need to test if we're still logged in
            self._client.ping()
        except freeipa.exceptions.Unauthorized as e:
            try:            
                self._client.login(
                    config.accounts.freeipa.username,
                    config.accounts.freeipa.password
                )
            except freeipa.exceptions.Unauthorized as e:
                logger.info("Login failed")
                raise exceptions.provider.Unavailable("Bad login credentials for account provider")

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info(f"freeipa session handle was held for {self.nonce}: {time.time() - self.t}")

class FreeIPA:    
    _client : freeipa.ClientMeta

    def __init__(self):
        logger.info("FreeIPA provider created")
        
        self._client = freeipa.ClientMeta(
            host=config.accounts.freeipa.server,
            dns_discovery=False,
            verify_ssl=False,
            request_timeout=2
        )

        self._client.login(
            config.accounts.freeipa.username,
            config.accounts.freeipa.password
        )

        logger.info("Ensuring groups setup in FreeIPA")
        with self._session():
            for group in models.group.groups:
                if not self._group_exists(group.group_name):
                    logger.info(f"Group {group.group_name} not found, adding", group=group)
                    self._client.group_add(
                        a_cn = group.group_name,
                        o_description = group.description,
                        o_gidnumber = group.gid
                    )

    def _session(self):
        return FreeIPASession(self._client)

    def change_password(
        self,
        account: models.account.Account, 
        password: models.password.Password
    ):
        with self._session():
            return self._change_password(account, password)

    def _change_password(
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
            self._client.user_mod(a_uid=find['result'][0]['uid'][0], o_krbpasswordexpiration="20381231011529Z")

        elif find2['count'] > 0:
            self._client.stageuser_mod(a_uid=find2['result'][0]['uid'][0], o_userpassword=password)

            self._client.change_password(account.username, password, password)
            self._client.stageuser_mod(a_uid=find2['result'][0]['uid'][0], o_krbpasswordexpiration="20381231011529Z")
        else:
            raise exceptions.resource.NotFound("could not find user account")

    def find_account(
        self,
        email_or_username: str
    ) -> models.account.Account:
        with self._session():
            return self._find_account(email_or_username)

    def _find_account(
        self,
        email_or_username: str
    ) -> models.account.Account:
        account = None 

        if self._username_exists(email_or_username):
            account = self._read_account_by_username(email_or_username)
        elif self._email_exists(email_or_username):
            account = self._read_account_by_email(email_or_username)

        if account is None:
            raise exceptions.resource.NotFound("could not find user account")
        
        return account
    
    def find_verified_account(
        self,
        email_or_username: str
    ) -> models.account.Account:
        with self._session():
            account = self._find_account(email_or_username)

            if account.verified is False:
                raise exceptions.resource.NotFound("An account was found but it is not verified")
            
            return account

    def username_exists(
        self,
        username: models.account.Username
    ) -> bool:
        with self._session():
            return self._username_exists(username)

    def _username_exists(
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
        with self._session():
            return self._email_exists(email)

    def _email_exists(
        self,
        email: EmailStr
    ) -> bool:
        res = self._client.user_find(o_mail=email)
        res2 = self._client.stageuser_find(o_mail=email)
        return (res['count'] > 0 or res2['count'] > 0)

    def group_exists(
        self,
        group_name: models.group.GroupName
    ) -> bool:
        with self._session():
            return self._group_exists(group_name)

    def _group_exists(
        self,
        group_name: models.group.GroupName
    ) -> bool:
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
        with self._session():
            return self._read_account_by_username(username)

    def _read_account_by_username(
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
            raise exceptions.resource.NotFound("could not find user account")

    def read_account_by_email(
        self,
        email : EmailStr
    ) -> models.account.Account:
        with self._session():
            return self._read_account_by_email(email)

    def _read_account_by_email(
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
            raise exceptions.resource.NotFound("could not find user account")


    def read_accounts_all(
        self
    ) -> Dict[str, models.account.Account]:
        with self._session():
            find = self._client.user_find()
            find2 = self._client.stageuser_find()

            accounts = self._populate_accounts_from_user_find(find)
            staged_accounts = self._populate_accounts_from_stageuser_find(find2)

            return {**staged_accounts, **accounts}

    def create_account(
        self,
        sign_up
    ):
        with self._session():
            if self._username_exists(sign_up.username):
                raise exceptions.resource.AlreadyExists("account already exists with this username")

            if self._email_exists(sign_up.username):
                raise exceptions.resource.AlreadyExists("account already exists with this email")

            if self._group_exists(sign_up.username):
                raise exceptions.resource.AlreadyExists("group already exists with this username")

            home_dir = Path(f"{config.accounts.home_dirs.resolve()}/{sign_up.username}")

            # if home_dir.is_symlink():
            #     raise exceptions.resource.AlreadyExists("home directory already exists as a symlink")
            
            # if home_dir.exists():
            #     raise exceptions.resource.AlreadyExists("home directory already exists")

            self._client.stageuser_add(
                a_uid=sign_up.username,
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
        account: models.account.Account,
        password: str
    ):
        """
        Activates an account
        """

        with self._session():
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

            account = self._read_account_by_username(account.username)

            # Set their password
            self._change_password(account, password)

    def read_gdpr_data(
        self,
        account: models.account.Account
    ) -> dict:
        with self._session():
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
