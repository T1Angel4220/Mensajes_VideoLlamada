from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contacts (
    owner_id INTEGER NOT NULL,
    contact_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (owner_id, contact_id),
    FOREIGN KEY (owner_id) REFERENCES users(id),
    FOREIGN KEY (contact_id) REFERENCES users(id),
    CHECK (owner_id != contact_id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_messages_pair
    ON messages(sender_id, receiver_id, created_at);

CREATE TABLE IF NOT EXISTS calls (
    id TEXT PRIMARY KEY,
    caller_id INTEGER NOT NULL,
    callee_id INTEGER NOT NULL,
    caller_name TEXT NOT NULL,
    callee_name TEXT NOT NULL,
    status TEXT NOT NULL,
    offer_type TEXT,
    offer_sdp TEXT,
    answer_type TEXT,
    answer_sdp TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (caller_id) REFERENCES users(id),
    FOREIGN KEY (callee_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS ice_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id TEXT NOT NULL,
    sender_id INTEGER NOT NULL,
    candidate TEXT NOT NULL,
    sdp_mid TEXT,
    sdp_m_line_index INTEGER,
    FOREIGN KEY (call_id) REFERENCES calls(id)
);
"""


def connect(path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=15, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = connect(path)
    try:
        connection.executescript(SCHEMA)
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()


@contextmanager
def get_connection(path: str) -> Iterator[sqlite3.Connection]:
    connection = connect(path)
    try:
        yield connection
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()
