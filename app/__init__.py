from __future__ import annotations

import os
import secrets
from pathlib import Path

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from app.persistence.db import init_db
from app.security.headers import register_security_headers
from app.security.lockout import AttemptTracker
from app.security.logging_security import configure_logging
from app.web.routes import register_routes

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
WEB_DIR = APP_DIR / "web"
SIGNING_ENV = "APP_SESSION_SIGNING_KEY"
csrf = CSRFProtect()


def _load_signing_key() -> str:
    env_key = os.environ.get(SIGNING_ENV)
    if env_key:
        return env_key
    return secrets.token_hex(32)


def _allow_plain_http(test_config: dict | None) -> bool:
    if test_config and test_config.get("TESTING"):
        return True
    return os.environ.get("APP_ALLOW_HTTP") == "1"


def create_app(test_config: dict | None = None) -> Flask:
    configure_logging()
    app = Flask(
        __name__,
        template_folder=str(WEB_DIR / "templates"),
        static_folder=str(WEB_DIR / "static"),
    )
    allow_http = _allow_plain_http(test_config)
    app.secret_key = _load_signing_key()
    app.config["DATABASE"] = str(BASE_DIR / "mensajes.db")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = not allow_http
    app.config["MAX_CONTENT_LENGTH"] = 256 * 1024
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_SSL_STRICT"] = not allow_http
    app.config["WTF_CSRF_TIME_LIMIT"] = 3600
    app.config["LOCKOUT"] = AttemptTracker()

    if test_config:
        app.config.update(test_config)
        testing_key = test_config.get("TESTING_SIGNING_KEY")
        if testing_key:
            app.secret_key = testing_key
        if "LOCKOUT" not in test_config:
            app.config["LOCKOUT"] = AttemptTracker()

    csrf.init_app(app)
    register_security_headers(app)
    init_db(app.config["DATABASE"])
    register_routes(app)
    return app
