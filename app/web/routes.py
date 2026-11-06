from __future__ import annotations

from flask import (
    Flask,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf.csrf import generate_csrf

from app.web import call_http
from app.domain.errors import (
    AuthLockedError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.chat.services import (
    add_contact,
    authenticate_user,
    list_contacts,
    load_conversation,
    register_user,
    send_text,
)
from app.web.common import login_required, uow

AUTH_TEMPLATE = "auth.html"


def _credentials() -> tuple[str, str]:
    return request.form.get("username", ""), request.form.get("password", "")


def _iniciar_sesion(user_id: int, username: str) -> None:
    session.clear()
    session["user_id"] = user_id
    session["username"] = username


def index():
    if "user_id" in session:
        return redirect(url_for("chat"))
    return redirect(url_for("login"))


def registro_get():
    return render_template(AUTH_TEMPLATE, modo="registro")


def registro_post():
    username, password = _credentials()
    try:
        with uow() as work:
            user = register_user(work.users, username, password)
        _iniciar_sesion(user.id, user.username)
        return redirect(url_for("chat"))
    except ValidationError as exc:
        flash(str(exc), "error")
        return render_template(AUTH_TEMPLATE, modo="registro")


def login_get():
    return render_template(AUTH_TEMPLATE, modo="login")


def login_post():
    username, password = _credentials()
    try:
        with uow() as work:
            user = authenticate_user(
                work.users, current_app.config["LOCKOUT"], username, password
            )
        _iniciar_sesion(user.id, user.username)
        return redirect(url_for("chat"))
    except AuthLockedError as exc:
        flash(str(exc), "error")
        return render_template(AUTH_TEMPLATE, modo="login"), 429
    except UnauthorizedError as exc:
        flash(str(exc), "error")
        return render_template(AUTH_TEMPLATE, modo="login")


def logout():
    session.clear()
    return redirect(url_for("login"))


@login_required
def chat():
    with uow() as work:
        contacts = list_contacts(work.contacts, session["user_id"])
    return render_template(
        "chat.html",
        username=session["username"],
        contacts=contacts,
        csrf_token=generate_csrf(),
    )


@login_required
def api_contactos():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON inválido."}), 400
    username = str(payload.get("username", "")).strip()
    try:
        with uow() as work:
            contact = add_contact(work.users, work.contacts, session["user_id"], username)
        return jsonify({"id": contact.id, "username": contact.username}), 201
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400


@login_required
def api_mensajes():
    other_name = request.args.get("con", "").strip()
    if not other_name:
        return jsonify({"error": "Indica el usuario destino."}), 400
    try:
        with uow() as work:
            items = load_conversation(
                work.users, work.contacts, work.messages, session["user_id"], other_name
            )
        return jsonify({"messages": items})
    except ForbiddenError as exc:
        return jsonify({"error": str(exc)}), 403
    except NotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400


@login_required
def api_enviar():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON inválido."}), 400
    other_name = str(payload.get("para", "")).strip()
    body = str(payload.get("texto", ""))
    if not other_name:
        return jsonify({"error": "Indica el destinatario."}), 400
    try:
        with uow() as work:
            message_id, sender = send_text(
                work.users,
                work.contacts,
                work.messages,
                session["user_id"],
                other_name,
                body,
            )
        return jsonify({"id": message_id, "sender": sender, "body": body.strip()}), 201
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400


def register_routes(app: Flask) -> None:
    app.add_url_rule("/", view_func=index)
    app.add_url_rule("/registro", endpoint="registro", view_func=registro_get, methods=["GET"])
    app.add_url_rule("/registro", endpoint="registro_post", view_func=registro_post, methods=["POST"])
    app.add_url_rule("/login", endpoint="login", view_func=login_get, methods=["GET"])
    app.add_url_rule("/login", endpoint="login_post", view_func=login_post, methods=["POST"])
    app.add_url_rule("/logout", view_func=logout, methods=["POST"])
    app.add_url_rule("/chat", view_func=chat)
    app.add_url_rule("/api/contactos", view_func=api_contactos, methods=["POST"])
    app.add_url_rule("/api/mensajes", view_func=api_mensajes, methods=["GET"])
    app.add_url_rule("/api/mensajes", endpoint="api_enviar", view_func=api_enviar, methods=["POST"])
    app.add_url_rule("/api/llamadas", view_func=call_http.api_crear_llamada, methods=["POST"])
    app.add_url_rule(
        "/api/llamadas/entrantes",
        view_func=call_http.api_llamadas_entrantes,
        methods=["GET"],
    )
    app.add_url_rule("/api/llamadas/<call_id>", view_func=call_http.api_obtener_llamada)
    app.add_url_rule(
        "/api/llamadas/<call_id>/oferta",
        view_func=call_http.api_oferta_llamada,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/llamadas/<call_id>/respuesta",
        view_func=call_http.api_respuesta_llamada,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/llamadas/<call_id>/ice",
        endpoint="api_listar_ice",
        view_func=call_http.api_listar_ice,
        methods=["GET"],
    )
    app.add_url_rule(
        "/api/llamadas/<call_id>/ice",
        endpoint="api_agregar_ice",
        view_func=call_http.api_agregar_ice,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/llamadas/<call_id>/colgar",
        view_func=call_http.api_colgar_llamada,
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/llamadas/<call_id>/rechazar",
        view_func=call_http.api_rechazar_llamada,
        methods=["POST"],
    )
