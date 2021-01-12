import os
import errno
from pathlib import Path
from typing import Dict
import structlog as logging
import stat
import python_freeipa as freeipa
import requests
import cachetools
import time
import cachetools
import inspect

from pydantic import EmailStr
from v1 import models, exceptions
from v1.config import config

logger = logging.getLogger(__name__)

import warnings

# Toggles error given off by FreeIPA
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class FreeIPA:    
    _client_instance : freeipa.ClientMeta = None
    _session_timer: int = 0

    _account_cache: cachetools.TTLCache
    _group_cache: cachetools.TTLCache


    def __init__(self):
        logger.info("FreeIPA provider created")
        
        logger.info("Ensuring groups setup in FreeIPA")

        self._group_cache = cachetools.TTLCache(maxsize=16, ttl=300)
        self._account_cache = cachetools.TTLCache(maxsize=100, ttl=90)

        for group in models.group.groups:
            if not self.group_exists(group.group_name):
                logger.info(f"Group {group.group_name} not found, adding", group=group)
                self._client.group_add(
                    a_cn = group.group_name,
                    o_description = group.description,
                    o_gidnumber = group.gid
                )

    @property
    def _client(self):
        if self._client_instance is None:
            self._client_instance = freeipa.ClientMeta(
                host=config.accounts.freeipa.server,
                dns_discovery=False,
                verify_ssl=False
            )
            self._session_timer = time.time()

            self._client_instance.login(
                config.accounts.freeipa.username,
                config.accounts.freeipa.password
            )

        # The FreeIPA session can expire every 15 minutes so we need to test if we're still logged in
        try:
            if (self._session_timer - time.time()) > (5*60):
                # ping and see if the session has expired
                self._session_timer = time.time()
                self._client_instance.ping()
        except freeipa.exceptions.Unauthorized as e: # expired session
            try:            
                self._client_instance.login(
                    config.accounts.freeipa.username,
                    config.accounts.freeipa.password
                )
            except freeipa.exceptions.Unauthorized as e:
                logger.info("Login failed to FreeIPA")
                raise exceptions.provider.Unavailable("Bad login credentials for account provider")
        
        return self._client_instance
        
    def change_password(
        self,
        account: models.account.Account, 
        password: models.password.Password
    ):
        if account.verified is True:
            find = self._client.user_find(
                o_uid=account.username
            )

            if find['count'] > 0:
                self._client.user_mod(a_uid=find['result'][0]['uid'][0], o_userpassword=password)
                self._client.change_password(account.username, password, password)
                self._client.user_mod(a_uid=find['result'][0]['uid'][0], o_krbpasswordexpiration="20381231011529Z")

                return 

        else:
            find2 = self._client.stageuser_find(
                o_uid=account.username
            )

            if find2['count'] > 0:
                self._client.stageuser_mod(a_uid=find2['result'][0]['uid'][0], o_userpassword=password)
                self._client.change_password(account.username, password, password)
                self._client.stageuser_mod(a_uid=find2['result'][0]['uid'][0], o_krbpasswordexpiration="20381231011529Z")

                return

        raise exceptions.resource.NotFound("could not find user account")


    def find_account(
        self,
        email_or_username: str
    ) -> models.account.Account:
        account = None 

        try:
            return self.read_account_by_email(email_or_username)
        except exceptions.resource.NotFound:
            try:    
                return self.read_account_by_username(email_or_username)
            except exceptions.resource.NotFound:
                raise exceptions.resource.NotFound("could not find user account")
    
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
        if username in self._account_cache:
            return True

        res = self._client.user_find(o_uid=username)
        
        if res['count'] > 0:
            return True

        res2 = self._client.stageuser_find(o_uid=username)

        if res2['count'] > 0:
            return True

        return False

    def email_exists(
        self,
        email: EmailStr
    ) -> bool:
        if email in self._account_cache:
            return True

        res = self._client.user_find(o_mail=email)

        if res['count'] > 0:
            return True

        res2 = self._client.stageuser_find(o_mail=email)

        if res2['count'] > 0:
            return True

        return False

    def group_exists(
        self,
        group_name: models.group.GroupName
    ) -> bool:
        try:
            self.read_group_by_name(group_name)
            return True
        except exceptions.resource.NotFound:
            return False

    def read_group_by_name(
        self,
        name: models.group.GroupName
    ) -> models.group.Group:
        if name in self._group_cache:
            return self._group_cache[name]

        group_find = self._client.group_find(o_cn=name)
 
        if group_find['count'] != 0:
            if 'posixgroup' in group_find['result'][0]['objectclass']:
                description = None
                if 'description' in group_find['result'][0]:
                    description = group_find['result'][0]['description'][0]

                return models.group.Group(
                    group_name = name,
                    description = description,
                    gid = group_find['result'][0]['gidnumber'][0]
                )
            else:
                return models.group.Group(
                    group_name = name
                )

            return group
        
        raise exceptions.resource.NotFound(f"could not find group {name}")

    def _populate_accounts_from_user_find(self, find) -> Dict[str, models.account.Account]:
        if find['count'] == 0:
            return {}   

        accounts = {}

        for i in range(find['count']):
            groups = {}
            
            for group_name in find['result'][i]['memberof_group']:
                groups[group_name] = self.read_group_by_name(group_name)

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
        if username in self._account_cache:
           return self._account_cache[username]

        find = self._client.user_find(
            o_uid=username
        )

        if find['count'] > 0:
            account = self._populate_accounts_from_user_find(find)[username]

            self._account_cache[account.username] = account
            return account

        find2 = self._client.stageuser_find(
            o_uid=username
        )

        if find2['count'] > 0:
            account = self._populate_accounts_from_stageuser_find(find2)[username]
            return account

        raise exceptions.resource.NotFound("could not find user account")

    def read_account_by_email(
        self,
        email : EmailStr
    ) -> models.account.Account:
        #if email in self._account_cache:
        #    return self._account_cache[email]

        find = self._client.user_find(
            o_mail=email
        )


        if find['count'] > 0:
            account = list(self._populate_accounts_from_user_find(find).items())[0][1]

            self._account_cache[email] = account
            return account

        find2 = self._client.stageuser_find(
            o_mail=email
        )

        if find2['count'] > 0:
            account = list(self._populate_accounts_from_stageuser_find(find2).items())[0][1]
            return account

        raise exceptions.resource.NotFound("could not find user account")


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

        # Set their password
        self._change_password(account, password)

    def read_gdpr_data(
        self,
        account: models.account.Account
    ) -> dict:
        find = self._client.user_find(
            o_mail=account.email,
            o_all=True
        )

        if find['count'] > 0:
            return find['result'][0]

        find2 = self._client.stageuser_find(
            o_mail=account.email,
            o_all=True
        )

        if find2['count'] > 0:
            return find2['result'][0]

        raise exceptions.resource.Unavailable("Account data could not be found")
