from __future__ import annotations

import pytest

from app.domain.errors import ValidationError
from app.domain.validation import (
    validate_message,
    validate_page_size,
    validate_password,
    validate_username,
)


def test_validaciones_ok():
    assert validate_username("ana_1") == "ana_1"
    assert validate_password("ClaveSegura1") == "ClaveSegura1"
    assert validate_message("  hola  ") == "hola"
    assert validate_page_size(None) == 100
    assert validate_page_size(10) == 10


def test_validaciones_error():
    with pytest.raises(ValidationError):
        validate_username("ab")
    with pytest.raises(ValidationError):
        validate_password("corta")
    with pytest.raises(ValidationError):
        validate_password("sinnumerosss")
    with pytest.raises(ValidationError):
        validate_password("1234567890")
    with pytest.raises(ValidationError):
        validate_password("con espacio1")
    with pytest.raises(ValidationError):
        validate_message("   ")
    with pytest.raises(ValidationError):
        validate_message("x" * 1001)
    with pytest.raises(ValidationError):
        validate_page_size(0)
    with pytest.raises(ValidationError):
        validate_page_size(101)
