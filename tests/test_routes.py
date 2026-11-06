from __future__ import annotations

import re

from app.security.lockout import AttemptTracker

PASSWORD = "ClaveSegura1"


def csrf_from(response) -> str:
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    if match:
        return match.group(1).decode()
    match = re.search(rb'name="csrf-token" content="([^"]+)"', response.data)
    if not match:
        raise AssertionError("No se encontró el token CSRF")
    return match.group(1).decode()


def registrar(client, username, password=PASSWORD):
    token = csrf_from(client.get("/registro"))
    return client.post(
        "/registro",
        data={"username": username, "password": password, "csrf_token": token},
        follow_redirects=True,
    )


def login(client, username, password=PASSWORD):
    token = csrf_from(client.get("/login"))
    return client.post(
        "/login",
        data={"username": username, "password": password, "csrf_token": token},
    )


def test_csrf_rechazado(client):
    respuesta = client.post("/login", data={"username": "ana", "password": PASSWORD})
    assert respuesta.status_code == 400


def test_cabeceras_seguridad(client):
    respuesta = client.get("/login")
    assert respuesta.headers["X-Content-Type-Options"] == "nosniff"
    assert respuesta.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in respuesta.headers["Content-Security-Policy"]


def test_flujo_mensajes(client):
    assert client.get("/").status_code == 302
    page = client.get("/login")
    assert page.status_code == 200
    bad = login(client, "nadie", PASSWORD)
    assert b"incorrectos" in bad.data

    registrar(client, "ana")
    chat_page = client.get("/chat")
    client.post("/logout", data={"csrf_token": csrf_from(chat_page)})
    registrar(client, "luis")
    lista = client.get("/chat")
    csrf = csrf_from(lista)

    alta = client.post(
        "/api/contactos",
        json={"username": "ana"},
        headers={"X-CSRFToken": csrf},
    )
    assert alta.status_code == 201

    enviado = client.post(
        "/api/mensajes",
        json={"para": "ana", "texto": "Hola desde Luis"},
        headers={"X-CSRFToken": csrf},
    )
    assert enviado.status_code == 201
    chat = client.get("/api/mensajes?con=ana")
    assert chat.get_json()["messages"][0]["body"] == "Hola desde Luis"

    xss = client.post(
        "/api/mensajes",
        json={"para": "ana", "texto": "<script>alert(1)</script>"},
        headers={"X-CSRFToken": csrf},
    )
    assert xss.status_code == 201
    stored = client.get("/api/mensajes?con=ana").get_json()["messages"][-1]["body"]
    assert stored == "<script>alert(1)</script>"

    error = client.post(
        "/api/mensajes",
        json={"para": "ana", "texto": "   "},
        headers={"X-CSRFToken": csrf},
    )
    assert error.status_code == 400
    sin_destino = client.post(
        "/api/mensajes",
        json={"texto": "hola"},
        headers={"X-CSRFToken": csrf},
    )
    assert sin_destino.status_code == 400
    invalido = client.post(
        "/api/mensajes",
        data="no-json",
        headers={"X-CSRFToken": csrf, "Content-Type": "application/json"},
    )
    assert invalido.status_code == 400


def test_idor_y_api_sin_sesion(client):
    registrar(client, "ana")
    client.post("/logout", data={"csrf_token": csrf_from(client.get("/chat"))})
    registrar(client, "luis")
    client.post("/logout", data={"csrf_token": csrf_from(client.get("/chat"))})
    registrar(client, "maria")
    csrf = csrf_from(client.get("/chat"))
    client.post("/api/contactos", json={"username": "luis"}, headers={"X-CSRFToken": csrf})
    propia = client.get("/api/mensajes?con=luis")
    assert propia.status_code == 200
    ajena = client.get("/api/mensajes?con=ana")
    assert ajena.status_code == 403
    sin_permiso = client.get("/api/mensajes?con=ghost")
    assert sin_permiso.status_code in {400, 404}
    client.post("/logout", data={"csrf_token": csrf})
    no_auth = client.get("/api/mensajes?con=ana")
    assert no_auth.status_code == 401
    chat = client.get("/chat", follow_redirects=False)
    assert chat.status_code == 302


def test_login_lockout_http(client, app):
    app.config["LOCKOUT"] = AttemptTracker(max_failures=3, window_seconds=60)
    registrar(client, "ana")
    client.post("/logout", data={"csrf_token": csrf_from(client.get("/chat"))})
    for _ in range(3):
        login(client, "ana", "MalaClave99")
    locked = login(client, "ana", PASSWORD)
    assert locked.status_code == 429


def test_contacto_json_invalido(client):
    registrar(client, "ana")
    csrf = csrf_from(client.get("/chat"))
    respuesta = client.post(
        "/api/contactos",
        data="no-json",
        headers={"X-CSRFToken": csrf, "Content-Type": "application/json"},
    )
    assert respuesta.status_code == 400


def test_registro_invalido(client):
    token = csrf_from(client.get("/registro"))
    fallo = client.post(
        "/registro",
        data={"username": "ab", "password": PASSWORD, "csrf_token": token},
    )
    assert fallo.status_code == 200
