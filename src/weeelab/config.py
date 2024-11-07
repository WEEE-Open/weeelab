from tomllib import load

from .constants import CONFIG_PATH


def load_config():
    with open(CONFIG_PATH, "rb") as f:
        return load(f)


config = load_config()
