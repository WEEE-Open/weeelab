import logging
import sys
from logging import getLogger

from actions import ask_action, login, logout

from .constants import VERSION


def help():
    print("Usage: weeelab [OPTIONS]")
    print("Options:")
    print("  -h, --help  Show this message and exit")
    print("  -v, --version   Show the version and exit")
    print("  -d, --debug     print all logs")


def main():
    if any([x in sys.argv for x in ["help", "--help", "-h"]]):
        help()
        sys.exit(0)

    if any([x in sys.argv for x in ["version", "--version", "-v"]]):
        print(f"weeelab v{VERSION} - WEEE Open")
        sys.exit(0)

    if any([x in sys.argv for x in ["debug", "--debug", "-d"]]):
        LOGGING_LEVEL = logging.DEBUG
    else:
        LOGGING_LEVEL = logging.INFO

    # Configure logger
    logger = getLogger(__name__)
    logger.setLevel(LOGGING_LEVEL)

    ch = logging.StreamHandler()
    ch.setLevel(LOGGING_LEVEL)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if "login" in sys.argv:
        action = "login"
    elif "logout" in sys.argv:
        action = "logout"

    if not action:
        action = ask_action()

    if action == "login":
        login()
    elif action == "logout":
        logout()
