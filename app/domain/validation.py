from __future__ import annotations

import string

from app.domain.errors import ValidationError

USERNAME_CHARS = set(string.ascii_letters + string.digits + "_")
MIN_PASSWORD_LENGTH = 10
MAX_MESSAGE_LENGTH = 1000
MAX_PAGE_SIZE = 100


def validate_username(username: str) -> str:
    cleaned = username.strip()
    if not 3 <= len(cleaned) <= 20 or not set(cleaned).issubset(USERNAME_CHARS):
        raise ValidationError(
            "El usuario debe tener entre 3 y 20 caracteres (letras, números o _)."
        )
    return cleaned


def validate_password(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError("La contraseña debe tener al menos 10 caracteres.")
    if any(character.isspace() for character in password):
        raise ValidationError("La contraseña no debe contener espacios.")
    has_letter = any(character.isalpha() for character in password)
    has_digit = any(character.isdigit() for character in password)
    if not has_letter or not has_digit:
        raise ValidationError("La contraseña debe incluir letras y números.")
    return password


def validate_message(body: str) -> str:
    cleaned = body.strip()
    if not cleaned:
        raise ValidationError("El mensaje no puede estar vacío.")
    if len(cleaned) > MAX_MESSAGE_LENGTH:
        raise ValidationError("El mensaje no puede superar 1000 caracteres.")
    return cleaned


def validate_page_size(size: int | None) -> int:
    if size is None:
        return MAX_PAGE_SIZE
    if size < 1 or size > MAX_PAGE_SIZE:
        raise ValidationError("El tamaño de página debe estar entre 1 y 100.")
    return size
