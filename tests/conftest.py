from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "TESTING_SIGNING_KEY": "test-signing-key-not-for-production",
            "DATABASE": str(tmp_path / "test.db"),
        }
    )
    return application


@pytest.fixture()
def client(app):
    return app.test_client()
