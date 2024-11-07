"""
Define the functions:
 - login()
 - logout()

 These connect with LDAP and perform the login and use the db module to interact with the database.
"""

import time
from dataclasses import dataclass

import ldap
from ldap.filter import escape_filter_chars

from . import db
from .config import config
from .exceptions import (DBConnectionError, LdapError, UserLoggedInError,
                         UserNotFoundError, UserNotLoggedInError)


@dataclass
class User:
    username: str
    full_name: str
    first_name: str
    signed_sir: bool


def matricolize(username: str):
    if username.isdigit():
        return f"s{username}"
    if username[1:].isdigit() and username[0] in ["s", "S", "d", "D"]:
        return username
    return None


def get_user(username: str) -> User:
    found = False
    ambiguous = False
    matricolized = matricolize(username)
    username = escape_filter_chars(username)
    if matricolized is None:
        filters = (
            f"(&(objectClass=weeeOpenPerson)(uid={username})(!(nsaccountlock=true)))",
            f"(&(objectClass=weeeOpenPerson)(weeelabnickname={username})(!(nsaccountlock=true)))",
        )
    else:
        filters = (
            f"(&(objectClass=weeeOpenPerson)(schacpersonaluniquecode={matricolized})(!(nsaccountlock=true)))",
        )
    del matricolized

    try:
        conn = ldap.initialize(config["ldap"]["host"])
        conn.protocol_version = ldap.VERSION3
        if config["ldap"]["host"].startswith("ldap://"):
            conn.start_tls_s()
        conn.simple_bind_s(config["ldap"]["bind_dn"], config["ldap"]["password"])
    except (ldap.SERVER_DOWN, ldap.LDAPError):
        print(
            f"Cannot connect to LDAP server {config['ldap']['host']}. Please notify an admin."
        )
        raise LdapError

    for ldap_filter in filters:
        result = conn.search_s(
            config["ldap"]["tree"],
            ldap.SCOPE_SUBTREE,
            ldap_filter,
            ("uid", "cn", "givenname", "signedsir"),
        )
        if len(result) > 1:
            ambiguous = True
        if len(result) == 1:
            attr = result[0][1]
            if "signedsir" in attr:
                signed_sir = attr["signedsir"][0].decode().lower() == "true"
            else:
                signed_sir = False
            return User(
                attr["uid"][0].decode(),
                attr["cn"][0].decode(),
                attr["givenname"][0].decode(),
                signed_sir,
            )
    conn.unbind_s()

    if ambiguous:
        print(
            "Multiple accounts found for that username/matricola/nickname, try with another one."
        )
        raise UserNotFoundError
    if not found:
        print("Username not recognized. Maybe you misspelled it or you're an intruder.")
        raise UserNotFoundError


def print_sir_warning():
    red = "\033[41m\033[30m"
    yellow = "\033[41m\033[97m"
    border = "\033[103m"
    bold = ""  # "\033[1m"
    disagio = "\033[5m"
    underline = "\033[97m"
    reset = "\033[0m"
    print(f"{red}{bold}")
    print("                                                                          ")
    print("                                                                          ")
    print(f"                                 {border}                   {red}")
    print(
        f"                                 {border}  {red}               {border}  {red}"
    )
    print(
        f"                                 {border}  {yellow}{disagio} SIGN THE SIR!{reset}{red} {border}  {red}"
    )
    print(
        f"                                 {border}  {red}               {border}  {red}"
    )
    print(f"                                 {border}                   {red}")
    print("")
    print(
        f" This is mandatory and very important, you have to make {underline}4 signatures{reset}{red} on a boring form."
    )
    print(
        "              Ask someone else in lab or on Telegram to provide you the form."
    )
    print("")
    # print("\x1b[1;37;44m")
    print(reset)


def write_tmp_log(username: str, action: str, location_or_motivation: str):
    seconds = int(time.time())

    with open(config["tmp"]["path"], "a") as f:
        f.write(f"{action}-{username}-{seconds}-{location_or_motivation}\n")


def login(username: str, location: str = "lab"):
    """
    Retrieve the LDAP user.
    If the user is not in LDAP, raise an error.
    If the user didn't sign the sir, print a warning.
    Call the db.login function to log the user in.
    """
    try:
        user = get_user(username)
    except LdapError:
        print("Writing to the database anyway.")
        user = User(username, username, username, True)

    # Check if the user signed the SIR
    if not user.signed_sir:
        print_sir_warning()

    # login
    try:
        db.login(user.username, location)
    except DBConnectionError:
        print("Cannot connect to the database.")
        print("Writing to a temporary file.")
        write_tmp_log(username, "login", location)


def logout(username: str, message: str):
    """
    Retrieve the LDAP user.
    If the user is not in LDAP, return an error.
    Call the db.logout function to log the user out.
    """
    try:
        user = get_user(username)
    except LdapError:
        print("Writing to the database anyway.")
        user = User(username, username, username, True)

    try:
        db.logout(user, message)
    except DBConnectionError:
        print("Writing to a temporary file.")
        write_tmp_log(user.username, "logout", message)
    except UserNotFoundError:
        print("User not found in the database.")
    except UserNotLoggedInError:
        print("User not logged in.")
    else:
        print(f"Logout successful! Bye {user.full_name}!")
