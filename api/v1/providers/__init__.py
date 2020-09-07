
import os
from pathlib import Path

from v1 import exceptions
from . import accounts, websites, email, backups, mysql, mkhomedir

from v1.config import config

import os,signal

try:
  accounts = accounts.FreeIPA()
  websites = websites.HomeDirFolder()

  if config.production is True:
    email = email.SendGrid()
  else:
    email = email.Debug()

  mkhomedir = mkhomedir.MkDir()

  backups = backups.HomeDirFolder()
  mysql = mysql.MySQL()
except exceptions.provider.Unavailable as e:
  # Kills the docker container
  os.kill(0, signal.SIGINT)