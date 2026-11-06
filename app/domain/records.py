from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UserRecord:
    id: int
    username: str
    password_hash: str | None = None
