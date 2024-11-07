from toml import load

from .constants import CONFIG_PATH


def load_config():
    with open(CONFIG_PATH) as f:
        config = load(f)


config = load_config()
