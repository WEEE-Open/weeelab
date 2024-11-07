import psycopg2
from .config import config
import time

def connect():
    return psycopg2.connect(
        dbname=config["db"]["name"],
        user=config["db"]["user"],
        password=config["db"]["password"],
        host=config["db"]["host"],
        port=config["db"]["port"]
    )

def create_user(username: str):
    """
    Create a new user with the given username.
    """
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO "user" (id, seconds, inlab)
                    VALUES (%s, %s, %s)
                """, (username, 0, False))
                conn.commit()
    except psycopg2.IntegrityError:
        # User already exists
        pass

def get_user_inlab(cur, username: str):
    cur.execute('SELECT inlab FROM "user" WHERE id = %s', (username,))
    row = cur.fetchone()
    return row[0] if row else None

def login(username: str, location: str = "lab"):
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
            start_time = int(time.time())
            cur.execute("""
                INSERT INTO "audit" (userId, startTime, location)
                VALUES (%s, %s, %s)
            """, (username, start_time, location))
            conn.commit()

def logout(username: str, motivation: str = "", approved: bool = True):
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
            cur.execute("""
                SELECT id FROM "audit"
                WHERE userId = %s AND endTime IS NULL
                ORDER BY startTime DESC LIMIT 1
            """, (username,))
            audit_row = cur.fetchone()
            if audit_row is None:
                raise Exception("No active audit entry found for user.")
            audit_id = audit_row[0]
            end_time = int(time.time())
            cur.execute("""
                UPDATE "audit"
                SET endTime = %s, motivation = %s, approved = %s
                WHERE id = %s
            """, (end_time, motivation, audit_id, approved))
            conn.commit()