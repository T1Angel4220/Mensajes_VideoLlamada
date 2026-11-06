from __future__ import annotations

from app.calls.policy import CallAccessPolicy
from app.calls.service import CallService
from app.calls.sqlite_store import SqliteCallRepository
from app.persistence.db import get_connection
from app.persistence.repositories import SqliteContactStore, SqliteMessageStore, SqliteUserStore


class SqliteUnitOfWork:
    def __init__(self, database_path: str) -> None:
        self._database_path = database_path
        self.users: SqliteUserStore
        self.contacts: SqliteContactStore
        self.messages: SqliteMessageStore
        self.calls: CallService
        self._context = get_connection(database_path)

    def __enter__(self) -> SqliteUnitOfWork:
        connection = self._context.__enter__()
        self.users = SqliteUserStore(connection)
        self.contacts = SqliteContactStore(connection)
        self.messages = SqliteMessageStore(connection)
        self.calls = CallService(SqliteCallRepository(connection), CallAccessPolicy())
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool | None:
        return self._context.__exit__(exc_type, exc, traceback)
