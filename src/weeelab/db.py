"""
This module connects to grillo's database, for future compatibility.
The database is a postgresql db with the following schema:
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

import psycopg2
from .config import config

def connect():
    return psycopg2.connect(
        dbname=config["db"]["name"],
        user=config["db"]["user"],
        password=config["db"]["password"],
        host=config["db"]["host"],
        port=config["db"]["port"]
    )

def create_user(username: str):
    pass

def login(username: str, location: str = "lab"):
    """
    Check that the user is not logged in. If it is, throw an error.
    If the user doesn't exist, create it.
    Then, add an entry to the audit table.
    """
    pass

def logout(username: str, motivation: str = ""):
    """
    Check that the user is logged in. If it isn't, throw an error.
    Update the entry in the audit table.
    """
    pass
