from __future__ import annotations

import sqlite3
from typing import Protocol

from app.domain.errors import ValidationError
from app.domain.records import UserRecord
from app.domain.validation import MAX_PAGE_SIZE


class UserStore(Protocol):
    def create(self, username: str, password_hash: str) -> int: ...
    def find_by_id(self, user_id: int) -> UserRecord | None: ...
    def find_by_username(self, username: str) -> UserRecord | None: ...


class ContactStore(Protocol):
    def add(self, owner_id: int, contact_id: int) -> None: ...
    def exists(self, owner_id: int, contact_id: int) -> bool: ...
    def list_for(self, owner_id: int) -> list[UserRecord]: ...


class MessageStore(Protocol):
    def add(self, sender_id: int, receiver_id: int, body: str) -> int: ...
    def conversation(
        self, user_id: int, other_id: int, limit: int = MAX_PAGE_SIZE
    ) -> list[sqlite3.Row]: ...


class SqliteUserStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, username: str, password_hash: str) -> int:
        try:
            cursor = self._connection.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash),
            )
        except sqlite3.IntegrityError as exc:
            raise ValidationError("Ese nombre de usuario ya existe.") from exc
        if cursor.lastrowid is None:
            raise ValidationError("No se pudo crear el usuario.")
        return int(cursor.lastrowid)

    def find_by_id(self, user_id: int) -> UserRecord | None:
        row = self._connection.execute(
            "SELECT id, username, password_hash FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return _to_user(row)

    def find_by_username(self, username: str) -> UserRecord | None:
        row = self._connection.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return _to_user(row)


class SqliteContactStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, owner_id: int, contact_id: int) -> None:
        try:
            self._connection.execute(
                "INSERT INTO contacts (owner_id, contact_id) VALUES (?, ?)",
                (owner_id, contact_id),
            )
        except sqlite3.IntegrityError as exc:
            raise ValidationError("No se pudo agregar el contacto.") from exc

    def exists(self, owner_id: int, contact_id: int) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM contacts WHERE owner_id = ? AND contact_id = ?",
            (owner_id, contact_id),
        ).fetchone()
        return row is not None

    def list_for(self, owner_id: int) -> list[UserRecord]:
        rows = self._connection.execute(
            """
            SELECT u.id, u.username
            FROM contacts c
            JOIN users u ON u.id = c.contact_id
            WHERE c.owner_id = ?
            ORDER BY u.username COLLATE NOCASE
            """,
            (owner_id,),
        ).fetchall()
        return [
            UserRecord(id=row["id"], username=row["username"])
            for row in rows
        ]


class SqliteMessageStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, sender_id: int, receiver_id: int, body: str) -> int:
        cursor = self._connection.execute(
            "INSERT INTO messages (sender_id, receiver_id, body) VALUES (?, ?, ?)",
            (sender_id, receiver_id, body),
        )
        if cursor.lastrowid is None:
            raise ValidationError("No se pudo guardar el mensaje.")
        return int(cursor.lastrowid)

    def conversation(
        self, user_id: int, other_id: int, limit: int = MAX_PAGE_SIZE
    ) -> list[sqlite3.Row]:
        return self._connection.execute(
            """
            SELECT m.id, m.body, m.created_at, m.sender_id, m.receiver_id,
                   s.username AS sender
            FROM messages m
            JOIN users s ON s.id = m.sender_id
            WHERE (m.sender_id = ? AND m.receiver_id = ?)
               OR (m.sender_id = ? AND m.receiver_id = ?)
            ORDER BY m.id DESC
            LIMIT ?
            """,
            (user_id, other_id, other_id, user_id, limit),
        ).fetchall()


def _to_user(row: sqlite3.Row | None) -> UserRecord | None:
    if row is None:
        return None
    keys = set(row.keys())
    return UserRecord(
        id=row["id"],
        username=row["username"],
        password_hash=row["password_hash"] if "password_hash" in keys else None,
    )
