import sys
from importlib.resources import files
from logging import getLogger
from pathlib import Path

logger = getLogger(__name__)

VERSION = "1.5.0"

CONFIG_PATH = Path.home() / ".config" / "WEEE Open" / "weeelab" / "config.toml"
if not CONFIG_PATH.exists():
    # Use default config
    CONFIG_PATH = Path(files("weeelab")) / "config.toml"
logger.debug(f"Using config file: {CONFIG_PATH}")
