from __future__ import annotations

import uuid

from app.domain.errors import ValidationError


class CallId:
    def __init__(self, value: str) -> None:
        cleaned = value.strip()
        if not cleaned or len(cleaned) > 64:
            raise ValidationError("Identificador de llamada inválido.")
        self._value = cleaned

    @classmethod
    def generate(cls) -> CallId:
        return cls(uuid.uuid4().hex)

    @property
    def value(self) -> str:
        return self._value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CallId) and self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)


class Participant:
    def __init__(self, user_id: int, username: str) -> None:
        if user_id < 1:
            raise ValidationError("Participante inválido.")
        if not username.strip():
            raise ValidationError("El participante requiere un usuario.")
        self._user_id = user_id
        self._username = username.strip()

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username
