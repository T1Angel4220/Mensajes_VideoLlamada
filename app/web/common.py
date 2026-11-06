from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import current_app, jsonify, redirect, request, session, url_for

from app.persistence.unit_of_work import SqliteUnitOfWork


def uow() -> SqliteUnitOfWork:
    return SqliteUnitOfWork(current_app.config["DATABASE"])


def login_required(view: Callable):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "No autenticado"}), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped
