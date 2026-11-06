from __future__ import annotations

import logging

logger = logging.getLogger("mensajes.security")


def configure_logging() -> None:
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def auth_failed(username: str, reason: str) -> None:
    logger.warning("auth_failed user=%s reason=%s", username, reason)


def auth_locked(username: str) -> None:
    logger.warning("auth_locked user=%s", username)


def auth_success(username: str) -> None:
    logger.info("auth_success user=%s", username)
