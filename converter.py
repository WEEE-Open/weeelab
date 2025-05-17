"""
Function to convert the old log txt files to sql files
"""

from datetime import datetime
import os
from pathlib import Path
import traceback
import ldap
from ldap.filter import escape_filter_chars
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(os.path.realpath(__file__)), '.env'))

LDAP_HOST = os.getenv("LDAP_HOST")
LDAP_BIND_DN = os.getenv("LDAP_BIND_DN")
LDAP_PASSWORD = os.getenv("LDAP_PASSWORD")
LDAP_TREE = "ou=People,dc=weeeopen,dc=it"

users = {}
uuids = {}
new_lines = []

conn = ldap.initialize(LDAP_HOST)
conn.protocol_version = ldap.VERSION3
if LDAP_HOST.startswith("ldap://"):
    conn.start_tls_s()
conn.simple_bind_s(LDAP_BIND_DN, LDAP_PASSWORD)

def convert_to_sql(file):
    if isinstance(file, str):
        file = Path(file)

    with open(file, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        try:
            indatetime, exdatetime, duration = line[1:17], line[20:36], line[39:44]
            in_timestamp = int(
                datetime.strptime(indatetime, "%d/%m/%Y %H:%M").timestamp()
            )
            ex_timestamp = int(
                datetime.strptime(exdatetime, "%d/%m/%Y %H:%M").timestamp()
            )
            d_time = int(duration.split(":")[0])*60 + int(duration.split(":")[1])
            if d_time*60 != ex_timestamp - in_timestamp:
                raise ValueError(f"Duration does not match. Explicit is {duration}, but time difference is {(ex_timestamp - in_timestamp)//3600}:{(ex_timestamp - in_timestamp)//60 % 60}")
            user, task = line[47:-1].split("> :: ", 1)
            if user in uuids:
                uuid = uuids[user]
            else:
                uuid = get_uuid_from_user(user)
                uuids[user] = uuid

            new_lines.append((uuid, in_timestamp, ex_timestamp, task))
            if uuid not in users:
                users[uuid] = 0

            users[uuid] += ex_timestamp - in_timestamp

        except ValueError:
            print(f"Error in {file} at line {i+1}: {line}", end="")
            logger.exception(traceback.format_exc(0))

def get_uuid_from_user(user):
    # Get ldap uuid
    ldap_filter = f"(&(objectClass=weeeOpenPerson)(uid={escape_filter_chars(user)}))"


    result = conn.search_s(
        LDAP_TREE,
        ldap.SCOPE_ONELEVEL,
        ldap_filter,
        ("schacPersonalUniqueCode",),
    )
    if len(result) > 1:
        ambiguous = True
        logger.exception(f"Ambiguous search ({ldap_filter}): {result}")
    elif len(result) == 1:
        attr = result[0][1]
        uuid = attr["schacPersonalUniqueCode"][0].decode()
    return uuid


if __name__ == "__main__":
    print("INSERT INTO locations (name) VALUES ('lab');")

    for file in Path(".").glob("log*.txt"):
        convert_to_sql(file)
    conn.unbind_s()

    for user, seconds in users.items():
        print(f"INSERT INTO user (id, seconds, inlab) VALUES ('{user}', {seconds}, false);")

    for line in new_lines:
        print(f"INSERT INTO audit (userId, startTime, endTime, motivation, approved, location) VALUES ('{line[0]}', {line[1]}, {line[2]}, '{line[3]}', true, 'lab');")


