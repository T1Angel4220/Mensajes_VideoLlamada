from __future__ import annotations

from app.domain.errors import (
    AuthLockedError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.security.lockout import AttemptTracker
from app.security.logging_security import auth_failed, auth_locked, auth_success
from app.domain.passwords import hash_password, password_matches
from app.domain.records import UserRecord
from app.persistence.repositories import ContactStore, MessageStore, UserStore
from app.domain.validation import (
    validate_message,
    validate_page_size,
    validate_password,
    validate_username,
)


def register_user(users: UserStore, username: str, password: str) -> UserRecord:
    username = validate_username(username)
    password = validate_password(password)
    user_id = users.create(username, hash_password(password))
    return UserRecord(id=user_id, username=username)


def authenticate_user(
    users: UserStore,
    tracker: AttemptTracker,
    username: str,
    password: str,
) -> UserRecord:
    key = username.strip().lower() or "unknown"
    if tracker.is_locked(key):
        auth_locked(key)
        raise AuthLockedError("Cuenta temporalmente bloqueada por intentos fallidos.")
    user = users.find_by_username(username.strip())
    stored_hash = user.password_hash if user else None
    if user is None or stored_hash is None or not password_matches(stored_hash, password):
        tracker.register_failure(key)
        auth_failed(key, "invalid_credentials")
        raise UnauthorizedError("Usuario o contraseña incorrectos.")
    tracker.clear(key)
    auth_success(user.username)
    return UserRecord(id=user.id, username=user.username)


def add_contact(
    users: UserStore,
    contacts: ContactStore,
    owner_id: int,
    contact_username: str,
) -> UserRecord:
    contact_username = validate_username(contact_username)
    other = users.find_by_username(contact_username)
    if other is None:
        raise NotFoundError("El usuario no existe.")
    if other.id == owner_id:
        raise ValidationError("No puedes agregarte a ti mismo.")
    if contacts.exists(owner_id, other.id):
        raise ValidationError("Ese contacto ya está agregado.")
    contacts.add(owner_id, other.id)
    return UserRecord(id=other.id, username=other.username)


def list_contacts(contacts: ContactStore, owner_id: int) -> list[UserRecord]:
    return contacts.list_for(owner_id)


def send_text(
    users: UserStore,
    contacts: ContactStore,
    messages: MessageStore,
    sender_id: int,
    receiver_username: str,
    body: str,
) -> tuple[int, str]:
    body = validate_message(body)
    receiver_username = validate_username(receiver_username)
    receiver = users.find_by_username(receiver_username)
    if receiver is None:
        raise NotFoundError("El destinatario no existe.")
    if receiver.id == sender_id:
        raise ValidationError("No puedes enviarte un mensaje a ti mismo.")
    if not contacts.exists(sender_id, receiver.id):
        raise ValidationError("Debes agregar al contacto antes de escribirle.")
    sender = users.find_by_id(sender_id)
    sender_name = sender.username if sender else ""
    message_id = messages.add(sender_id, receiver.id, body)
    return message_id, sender_name


def load_conversation(
    users: UserStore,
    contacts: ContactStore,
    messages: MessageStore,
    user_id: int,
    other_username: str,
    limit: int | None = None,
) -> list[dict]:
    other_username = validate_username(other_username)
    page = validate_page_size(limit)
    other = users.find_by_username(other_username)
    if other is None:
        raise NotFoundError("El usuario no existe.")
    if not contacts.exists(user_id, other.id):
        raise ForbiddenError("No tienes permiso para ver esta conversación.")
    rows = list(reversed(messages.conversation(user_id, other.id, page)))
    return [
        {
            "id": row["id"],
            "body": row["body"],
            "sender": row["sender"],
            "mine": row["sender_id"] == user_id,
            "created_at": row["created_at"],
        }
        for row in rows
    ]
