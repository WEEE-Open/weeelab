"""
Function to convert the old log txt files to sql files
"""

from datetime import datetime
from pathlib import Path
import traceback
import ldap
from ldap.filter import escape_filter_chars
from weeelab import LDAP_BIND_DN, LDAP_PASSWORD

DRY_RUN = True
LDAP_HOST = "ldap://ldap.example.com"
LDAP_BIND_DN = "cn=something,dc=example,dc=com"
LDAP_PASSWORD = "foo"
LDAP_TREE = "ou=People,dc=example,dc=com"

users = set()

def convert_to_sql(file, dry_run=False):
    if isinstance(file, str):
        file = Path(file)

    with open(file, "r") as f:
        lines = f.readlines()

    sql_file = file.with_suffix(".sql")
    new_lines = []
    for i, line in enumerate(lines):
        try:
            indatetime, exdatetime, duration = line[1:17], line[20:36], line[39:44]
            in_timestamp = int(
                datetime.strptime(indatetime, "%d/%m/%Y %H:%M").timestamp()
            )
            ex_timestamp = int(
                datetime.strptime(exdatetime, "%d/%m/%Y %H:%M").timestamp()
            )
            d_time = duration.split(":")[0]*60 + duration.split(":")[1]
            if d_time*60 != ex_timestamp - in_timestamp:
                raise ValueError(f"Duration does not match. Explicit is {duration}, but time difference is {(ex_timestamp - in_timestamp)//3600}:{(ex_timestamp - in_timestamp)//60 % 60}")
            user, task = line[47:-1].split("> :: ", 1)
            new_lines.append(
                f"INSERT INTO audit (userId, startTime, endTime, motivation, approved, location) VALUES ('{user}', {in_timestamp}, {ex_timestamp}, '{task}', true, 'lab');\n"
            )
            users.add(user)
        except ValueError:
            print(f"Error in {file} at line {i}: {line}")
            print(traceback.format_exc(0))
            break
    else:
        if not dry_run:
            with open(sql_file, "w") as f:
                f.writelines(new_lines)


if __name__ == "__main__":
    for file in Path(".").glob("log*.txt"):
        convert_to_sql(file, DRY_RUN)

    new_lines = []
    for user in users:
        # Get ldap uuid
        filters = (
            f"(&(objectClass=weeeOpenPerson)(schacpersonaluniquecode={escape_filter_chars(user)})(!(nsaccountlock=true)))",
        )

        conn = ldap.initialize(LDAP_HOST)
        conn.protocol_version = ldap.VERSION3
        if LDAP_HOST.startswith("ldap://"):
            conn.start_tls_s()
        conn.simple_bind_s(LDAP_BIND_DN, LDAP_PASSWORD)


        for ldap_filter in filters:
            result = conn.search_s(
                LDAP_TREE,
                ldap.SCOPE_SUBTREE,
                ldap_filter,
                ("weeeopenuniqueid", "uid", "cn", "givenname", "signedsir"),
            )
            if len(result) > 1:
                ambiguous = True
            if len(result) == 1:
                attr = result[0][1]
                if "signedsir" in attr:
                    signed_sir = attr["signedsir"][0].decode().lower() == "true"
                else:
                    signed_sir = False
                uuid = attr["weeeopenuniqueid"][0].decode()
        conn.unbind_s()


        new_lines.append(f"INSERT INTO users (id, seconds, inlab) VALUES ('{uuid}', 0, false);\n")

    if not DRY_RUN:
        with open('init_db.sql', "a") as f:
            f.writelines(new_lines)
            f.write("INSERT INTO locations (name) VALUES ('lab');\n")