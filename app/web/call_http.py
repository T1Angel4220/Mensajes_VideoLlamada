from __future__ import annotations

from flask import jsonify, request, session

from app.calls.errors import CallConflictError
from app.domain.errors import ForbiddenError, NotFoundError, ValidationError
from app.domain.records import UserRecord
from app.web.common import login_required, uow


def _payload() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("JSON inválido.")
    return data


def _current_user(work) -> UserRecord:
    user = work.users.find_by_id(session["user_id"])
    if user is None:
        raise ForbiddenError("Sesión inválida.")
    return user


def _sdp_fields(data: dict) -> tuple[str, str, list[str] | None]:
    raw_lines = data.get("lines")
    lines = None
    if isinstance(raw_lines, list):
        lines = [str(item) for item in raw_lines]
    return str(data.get("type", "")), str(data.get("sdp", "")), lines


def _call_error(exc: Exception):
    if isinstance(exc, CallConflictError):
        return jsonify({"error": str(exc)}), 409
    if isinstance(exc, ForbiddenError):
        return jsonify({"error": str(exc)}), 403
    if isinstance(exc, NotFoundError):
        return jsonify({"error": str(exc)}), 404
    if isinstance(exc, ValidationError):
        return jsonify({"error": str(exc)}), 400
    raise exc


@login_required
def api_crear_llamada():
    try:
        data = _payload()
        with uow() as work:
            call = work.calls.start(
                work.users,
                work.contacts,
                _current_user(work),
                str(data.get("para", "")),
            )
            return jsonify(call.to_dict(session["user_id"])), 201
    except ValidationError as exc:
        return _call_error(exc)


@login_required
def api_llamadas_entrantes():
    with uow() as work:
        pending = work.calls.incoming(session["user_id"])
    return jsonify({"calls": [item.to_dict(session["user_id"]) for item in pending]})


@login_required
def api_obtener_llamada(call_id: str):
    try:
        with uow() as work:
            call = work.calls.get_for(call_id, session["user_id"])
            return jsonify(call.to_dict(session["user_id"]))
    except ValidationError as exc:
        return _call_error(exc)


@login_required
def api_oferta_llamada(call_id: str):
    return _signal(call_id, "offer")


@login_required
def api_respuesta_llamada(call_id: str):
    return _signal(call_id, "answer")


def _signal(call_id: str, action: str):
    try:
        kind, sdp, lines = _sdp_fields(_payload())
        with uow() as work:
            if action == "offer":
                call = work.calls.offer(call_id, session["user_id"], kind, sdp, lines)
            else:
                call = work.calls.answer(call_id, session["user_id"], kind, sdp, lines)
            return jsonify(call.to_dict(session["user_id"]))
    except ValidationError as exc:
        return _call_error(exc)


@login_required
def api_listar_ice(call_id: str):
    try:
        after = int(request.args.get("after", "0"))
    except ValueError:
        return jsonify({"error": "Parámetro after inválido."}), 400
    try:
        with uow() as work:
            items = work.calls.list_ice(call_id, session["user_id"], after)
        return jsonify({"candidates": [item.to_dict() for item in items]})
    except ValidationError as exc:
        return _call_error(exc)


@login_required
def api_agregar_ice(call_id: str):
    try:
        data = _payload()
        mid = data.get("sdpMid")
        index = data.get("sdpMLineIndex")
        with uow() as work:
            ice = work.calls.add_ice(
                call_id,
                session["user_id"],
                str(data.get("candidate", "")),
                None if mid is None else str(mid),
                None if index is None else int(index),
            )
        return jsonify(ice.to_dict()), 201
    except ValidationError as exc:
        return _call_error(exc)
    except (TypeError, ValueError):
        return jsonify({"error": "Candidato ICE inválido."}), 400


@login_required
def api_colgar_llamada(call_id: str):
    return _close(call_id, "hangup")


@login_required
def api_rechazar_llamada(call_id: str):
    return _close(call_id, "reject")


def _close(call_id: str, action: str):
    try:
        with uow() as work:
            if action == "hangup":
                call = work.calls.hang_up(call_id, session["user_id"])
            else:
                call = work.calls.reject(call_id, session["user_id"])
            return jsonify(call.to_dict(session["user_id"]))
    except ValidationError as exc:
        return _call_error(exc)
