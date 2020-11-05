
import os
import time
import time
import structlog as logging
import random

from pathlib import Path

from v1 import exceptions
from . import accounts, email, mkhomedir, proxmox

from v1.config import config

import os,signal

logger = logging.getLogger(__name__)

try:
  accounts = accounts.FreeIPA()

  if config.production is True:
    email = email.SendGrid()
  else:
    email = email.Debug()

  mkhomedir = mkhomedir.MkDir()

  proxmox = proxmox.Proxmox()

except exceptions.provider.Unavailable as e:
  # Kills the docker container
  t = random.randint(2,6)
  logger.critical(f"Providers unavailable, sleeping for {t} seconds")
  time.sleep(t)
  os.kill(0, signal.SIGINT)
