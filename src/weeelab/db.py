"""
This module connects to grillo's database, for future compatibility.
Check the full definition of the database at https://github.com/WEEE-Open/grillo/blob/master/docker/db/createTables.sql
The database is a postgresql db; these are the tables weeelab interacts with:
CREATE TABLE IF NOT EXISTS "user" (
    id VARCHAR(255) PRIMARY KEY NOT NULL,
    seconds INTEGER NOT NULL DEFAULT 0,
    inlab BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS "location" (
    id VARCHAR(255) PRIMARY KEY NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "audit" (
    id SERIAL PRIMARY KEY,
    userId VARCHAR(255) NOT NULL,
    startTime INTEGER NOT NULL,
    endTime INTEGER,
    motivation TEXT,
    approved BOOLEAN DEFAULT FALSE,
    location VARCHAR(255) NOT NULL,
    FOREIGN KEY(userId) REFERENCES "user"(id),
    FOREIGN KEY(location) REFERENCES "location"(id)
);


Note: user.id is the username, and location.id is the location name.
"""

import time

import psycopg2

from .config import config
from .exceptions import DBConnectionError


def connect():
    try:
        return psycopg2.connect(
            dbname=config["db"]["name"],
            user=config["db"]["user"],
            password=config["db"]["password"],
            host=config["db"]["host"],
            port=config["db"]["port"],
        )
    except psycopg2.OperationalError:
        raise DBConnectionError("Cannot connect to database. Please notify an admin")


def create_user(username: str):
    """
    Create a new user with the given username.
    """
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO "user" (id, seconds, inlab)
                    VALUES (%s, %s, %s)
                """,
                    (username, 0, False),
                )
                conn.commit()
    except psycopg2.IntegrityError:
        # User already exists
        pass


def get_user_inlab(cur, username: str):
    cur.execute('SELECT inlab FROM "user" WHERE id = %s', (username,))
    row = cur.fetchone()
    return row[0] if row else None


def login(username: str, location: str = "lab", seconds: int | None = None):
    """
    Check that the user is not logged in. If it is, throw an error.
    If the user doesn't exist, create it.
    Then, add an entry to the audit table.
    """
    with connect() as conn:
        with conn.cursor() as cur:
            inlab = get_user_inlab(cur, username)
            if inlab is None:
                # User doesn't exist, create it
                create_user(username)
                inlab = False
            if inlab:
                raise Exception("User is already logged in.")
            # Add entry to audit table
            if not seconds:
                seconds = int(time.time())
            cur.execute(
                """
                INSERT INTO "audit" (userId, startTime, location)
                VALUES (%s, %s, %s)
            """,
                (username, seconds, location),
            )
            conn.commit()


def logout(
    username: str,
    motivation: str = "",
    seconds: int | None = None,
    approved: bool = True,
):
    """
    Check that the user is logged in. If it isn't, throw an error.
    Update the entry in the audit table.
    """
    with connect() as conn:
        with conn.cursor() as cur:
            inlab = get_user_inlab(cur, username)
            if inlab is None:
                raise Exception("User does not exist.")
            if not inlab:
                raise Exception("User is not logged in.")

            # Update the audit entry
            cur.execute(
                """
                SELECT id FROM "audit"
                WHERE userId = %s AND endTime IS NULL
                ORDER BY startTime DESC LIMIT 1
            """,
                (username,),
            )
            audit_row = cur.fetchone()
            if audit_row is None:
                raise Exception("No active audit entry found for user.")
            audit_id = audit_row[0]
            if not seconds:
                seconds = int(time.time())
            cur.execute(
                """
                UPDATE "audit"
                SET endTime = %s, motivation = %s, approved = %s
                WHERE id = %s
            """,
                (seconds, motivation, audit_id, approved),
            )
            conn.commit()


def try_update():
    """
    Try to update the database from the temporary file.
    """
    try:
        with open(config["tmp"]["path"]) as f:
            for line in f:
                action, username, seconds, location_or_motivation = line.strip().split(
                    "-"
                )
                if action == "login":
                    login(
                        username,
                        location_or_motivation,
                        int(seconds),
                    )
                elif action == "logout":
                    logout(username, location_or_motivation, int(seconds))
        # Empty the file
        with open(config["tmp"]["path"], "w"):
            pass  # noqa

    except DBConnectionError:
        pass
