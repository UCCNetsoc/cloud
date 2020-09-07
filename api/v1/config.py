
import os
import yaml

from pathlib import Path

from v1 import models

config_path = Path(os.environ["CONFIG_FILE"] if "CONFIG_FILE" in os.environ else "/config.yml")
config = models.config.Config.parse_obj(yaml.safe_load(config_path.read_text()))