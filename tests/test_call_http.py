from __future__ import annotations

import re

PASSWORD = "ClaveSegura1"


def csrf_from(response) -> str:
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    if match:
        return match.group(1).decode()
    match = re.search(rb'name="csrf-token" content="([^"]+)"', response.data)
    if not match:
        raise AssertionError("No se encontró el token CSRF")
    return match.group(1).decode()


def registrar(client, username):
    token = csrf_from(client.get("/registro"))
    return client.post(
        "/registro",
        data={"username": username, "password": PASSWORD, "csrf_token": token},
        follow_redirects=True,
    )


def headers(client):
    return {"X-CSRFToken": csrf_from(client.get("/chat"))}


def test_flujo_http_videollamada(app):
    ana = app.test_client()
    luis = app.test_client()
    registrar(ana, "ana")
    registrar(luis, "luis")
    assert ana.post(
        "/api/contactos", json={"username": "luis"}, headers=headers(ana)
    ).status_code == 201

    sin_json = ana.post(
        "/api/llamadas", data="x", headers={**headers(ana), "Content-Type": "application/json"}
    )
    assert sin_json.status_code == 400

    prohibida = luis.post("/api/llamadas", json={"para": "ana"}, headers=headers(luis))
    assert prohibida.status_code == 403

    creada = ana.post("/api/llamadas", json={"para": "luis"}, headers=headers(ana))
    assert creada.status_code == 201
    call_id = creada.get_json()["id"]

    ajena = app.test_client()
    registrar(ajena, "maria")
    assert ajena.get(f"/api/llamadas/{call_id}").status_code == 403

    oferta = ana.post(
        f"/api/llamadas/{call_id}/oferta",
        json={"type": "offer", "sdp": "v=0 oferta-http"},
        headers=headers(ana),
    )
    assert oferta.status_code == 200
    entradas = luis.get("/api/llamadas/entrantes").get_json()["calls"]
    assert entradas[0]["id"] == call_id

    respuesta = luis.post(
        f"/api/llamadas/{call_id}/respuesta",
        json={"type": "answer", "sdp": "v=0 respuesta-http"},
        headers=headers(luis),
    )
    assert respuesta.get_json()["status"] == "in_call"

    ice = ana.post(
        f"/api/llamadas/{call_id}/ice",
        json={"candidate": "cand-1", "sdpMid": "0", "sdpMLineIndex": 0},
        headers=headers(ana),
    )
    assert ice.status_code == 201
    lista = luis.get(f"/api/llamadas/{call_id}/ice?after=0").get_json()["candidates"]
    assert lista[0]["candidate"] == "cand-1"
    assert luis.get(f"/api/llamadas/{call_id}/ice?after=x").status_code == 400

    colgar = ana.post(f"/api/llamadas/{call_id}/colgar", headers=headers(ana))
    assert colgar.get_json()["status"] == "ended"


def test_rechazo_http(app):
    ana = app.test_client()
    luis = app.test_client()
    registrar(ana, "ana")
    registrar(luis, "luis")
    ana.post("/api/contactos", json={"username": "luis"}, headers=headers(ana))
    call_id = ana.post(
        "/api/llamadas", json={"para": "luis"}, headers=headers(ana)
    ).get_json()["id"]
    rechazo = luis.post(f"/api/llamadas/{call_id}/rechazar", headers=headers(luis))
    assert rechazo.get_json()["status"] == "rejected"
    assert ana.get("/api/llamadas/nope").status_code == 404
    ausente = ana.post("/api/llamadas", json={"para": "ghost"}, headers=headers(ana))
    assert ausente.status_code == 404
    call_id = ana.post(
        "/api/llamadas", json={"para": "luis"}, headers=headers(ana)
    ).get_json()["id"]
    oferta_ajena = luis.post(
        f"/api/llamadas/{call_id}/oferta",
        json={"type": "offer", "sdp": "v=0 x"},
        headers=headers(luis),
    )
    assert oferta_ajena.status_code == 403
    ice_malo = ana.post(
        f"/api/llamadas/{call_id}/ice",
        json={"candidate": "c", "sdpMLineIndex": "no-int"},
        headers=headers(ana),
    )
    assert ice_malo.status_code == 400
