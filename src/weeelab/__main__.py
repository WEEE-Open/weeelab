import logging
import sys
from logging import getLogger
from pathlib import Path

from . import db
from .actions import login, logout
from .config import config
from .constants import COLOR_NATIVE, VERSION


def help():
    print("Usage: weeelab [OPTIONS]")
    print("Options:")
    print("  -h, --help      Show this message and exit")
    print("  -v, --version   Show the version and exit")
    print("  -d, --debug     print all logs")
    print("  -u, --user      Specify the user to login/logout.")
    print(
        "  -m, --message   Specify the message on logout. Implies logout, will be ignored if login is specified."
    )
    print("  -a, --action    Specify the action to perform. Can be login or logout.")


def parse_args():  # should move to argparse
    user = None
    action = None
    message = None
    logging_level = logging.INFO

    if any([x in sys.argv for x in ["help", "--help", "-h"]]):
        help()
        sys.exit(0)

    if any([x in sys.argv for x in ["version", "--version", "-v"]]):
        print(f"weeelab v{VERSION} - WEEE Open")
        sys.exit(0)

    if any([x in sys.argv for x in ["debug", "--debug", "-d"]]):
        logging_level = logging.DEBUG

    if any([x in sys.argv for x in ["user", "--user", "-u"]]):
        user = sys.argv[sys.argv.index("user") + 1]

    if any([x in sys.argv for x in ["message", "--message", "-m"]]):
        message = sys.argv[sys.argv.index("message") + 1]

    if any([x in sys.argv for x in ["action", "--action", "-a"]]):
        action = sys.argv[sys.argv.index("action") + 1]
        if action not in ["login", "logout"]:
            print("Invalid action. Must be login or logout.")
            sys.exit(1)

    return user, action, message, logging_level


def parse_new_format(text: str, delimiter: str):
    try:
        i = 0
        while 1:
            i = text.index(delimiter, i)
            if text[i + 1 : i + 5] == "0000" and len(text) > i + 15 + 1:
                return text[i + 9 : i + 15]
    except ValueError:
        return None


def parse_card_reader(text: str) -> str | None:
    if (text[0] == "ò" and text[-1] in ["-", "_"]) or (
        text[0] == ";" and text[-1] in ["/", "?"]
    ):
        matricola = text[9:15]
    else:
        matricola = parse_new_format(text, "ò")
        if not matricola:
            matricola = parse_new_format(text, ";")

    if matricola:
        print(f"Detected card scan with ID {matricola}")
    return matricola


def main():
    if Path(config["tmp"]["path"]).exists():
        db.try_update()

    interactive = False
    user, action, message, logging_level = parse_args()
    if any([user is None, action is None, action == "logout" and message is None]):
        interactive = True

    # Make sure the tmp file exists
    Path(config["tmp"]["path"]).parent.mkdir(parents=True, exist_ok=True)
    Path(config["tmp"]["path"]).touch(exist_ok=True)

    # Configure logger
    logger = getLogger(__name__)
    logger.setLevel(logging_level)

    ch = logging.StreamHandler()
    ch.setLevel(logging_level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    while not action:
        action = input("What do you want to do? [login | logout] :: ").lower()
        if action not in ["login", "logout"]:
            print("Invalid action. Must be login or logout.")
            action = None

    if not user:
        user = input(
            "Type your name.username OR student id (matricola) OR swipe the card on the reader: "
        )
        scanned_id = parse_card_reader(user)
        if scanned_id:
            user = scanned_id

    if action == "logout" and not message:
        message = input("Type the message to be saved on logout: ")

    if action == "login":
        login(user)
    elif action == "logout":
        logout(user, message)

    sys.stdout.write(COLOR_NATIVE)
    if interactive:
        print("Press enter to exit")
        # does this work on windows?
        input()
    sys.exit(0)
