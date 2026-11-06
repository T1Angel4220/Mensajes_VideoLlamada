from __future__ import annotations

import pytest

from app.persistence.db import get_connection
from app.domain.errors import (
    AuthLockedError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.security.lockout import AttemptTracker
from app.persistence.repositories import SqliteContactStore, SqliteMessageStore, SqliteUserStore
from app.chat.services import (
    add_contact,
    authenticate_user,
    load_conversation,
    register_user,
    send_text,
)


def test_registro_auth_contactos_y_mensajes(app):
    with get_connection(app.config["DATABASE"]) as connection:
        users = SqliteUserStore(connection)
        contacts = SqliteContactStore(connection)
        messages = SqliteMessageStore(connection)
        tracker = AttemptTracker(max_failures=3, window_seconds=60)
        ana = register_user(users, "ana", "ClaveSegura1")
        luis = register_user(users, "luis", "ClaveSegura1")
        maria = register_user(users, "maria", "ClaveSegura1")
        with pytest.raises(ValidationError):
            register_user(users, "ana", "ClaveSegura1")
        auth = authenticate_user(users, tracker, "ana", "ClaveSegura1")
        assert auth.id == ana.id
        with pytest.raises(UnauthorizedError):
            authenticate_user(users, tracker, "ana", "MalaClave99")
        add_contact(users, contacts, ana.id, "luis")
        send_text(users, contacts, messages, ana.id, "luis", "Hola Luis")
        chat = load_conversation(users, contacts, messages, ana.id, "luis")
        assert chat[0]["body"] == "Hola Luis"
        with pytest.raises(ValidationError):
            send_text(users, contacts, messages, ana.id, "maria", "sin contacto")
        with pytest.raises(ForbiddenError):
            load_conversation(users, contacts, messages, ana.id, "maria")
        with pytest.raises(ValidationError):
            send_text(users, contacts, messages, ana.id, "ana", "a mi")
        add_contact(users, contacts, luis.id, "maria")
        send_text(users, contacts, messages, luis.id, "maria", "secreto")
        with pytest.raises(ForbiddenError):
            load_conversation(users, contacts, messages, ana.id, "maria")


def test_lockout(app):
    with get_connection(app.config["DATABASE"]) as connection:
        users = SqliteUserStore(connection)
        tracker = AttemptTracker(max_failures=3, window_seconds=60)
        register_user(users, "ana", "ClaveSegura1")
        for _ in range(3):
            with pytest.raises(UnauthorizedError):
                authenticate_user(users, tracker, "ana", "MalaClave99")
        with pytest.raises(AuthLockedError):
            authenticate_user(users, tracker, "ana", "ClaveSegura1")


def test_contactos_invalidos(app):
    with get_connection(app.config["DATABASE"]) as connection:
        users = SqliteUserStore(connection)
        contacts = SqliteContactStore(connection)
        ana = register_user(users, "ana", "ClaveSegura1")
        register_user(users, "luis", "ClaveSegura1")
        with pytest.raises(NotFoundError):
            add_contact(users, contacts, ana.id, "ghost")
        with pytest.raises(ValidationError):
            add_contact(users, contacts, ana.id, "ana")
        add_contact(users, contacts, ana.id, "luis")
        with pytest.raises(ValidationError):
            add_contact(users, contacts, ana.id, "luis")
