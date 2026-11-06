from __future__ import annotations

import pytest

from app.calls.errors import CallConflictError
from app.calls.identity import CallId, Participant
from app.calls.model import Call
from app.calls.policy import CallAccessPolicy
from app.calls.service import CallService
from app.calls.signaling import IceCandidate, SessionDescription, join_sdp, sdp_lines
from app.calls.sqlite_store import SqliteCallRepository
from app.calls.status import CallStatus
from app.persistence.db import get_connection
from app.domain.errors import ForbiddenError, NotFoundError, ValidationError
from app.persistence.repositories import SqliteContactStore, SqliteUserStore
from app.chat.services import add_contact, register_user


PASSWORD = "ClaveSegura1"
OFFER = SessionDescription("offer", "v=0 offer-sdp")
ANSWER = SessionDescription("answer", "v=0 answer-sdp")


def test_sdp_se_normaliza_con_crlf():
    crudo = "v=0\na=ssrc:1 msid:stream track\n"
    desc = SessionDescription.from_payload("offer", crudo, sdp_lines(crudo))
    assert desc.sdp.endswith("\r\n")
    assert "\r\n" in desc.sdp
    assert desc.to_dict()["lines"][0] == "v=0"
    assert join_sdp(["v=0", "o=- 0 0 IN IP4 127.0.0.1"]).startswith("v=0\r\n")


def test_entidades_y_maquina_de_estados():
    call = Call(CallId.generate(), Participant(1, "ana"), Participant(2, "luis"))
    assert call.status is CallStatus.RINGING
    assert call.has_participant(1)
    call.place_offer(1, OFFER)
    assert call.status is CallStatus.OFFERING
    call.place_answer(2, ANSWER)
    assert call.status is CallStatus.IN_CALL
    call.hang_up(1)
    assert call.status is CallStatus.ENDED
    call.hang_up(1)
    with pytest.raises(CallConflictError):
        Call(CallId.generate(), Participant(1, "ana"), Participant(1, "ana"))
    with pytest.raises(ValidationError):
        CallId("  ")
    with pytest.raises(ValidationError):
        Participant(0, "ana")
    with pytest.raises(ValidationError):
        SessionDescription("pranswer", "sdp")
    with pytest.raises(ValidationError):
        IceCandidate("", None, None, 1)


def test_rechazo_y_acceso(app):
    with get_connection(app.config["DATABASE"]) as connection:
        users = SqliteUserStore(connection)
        contacts = SqliteContactStore(connection)
        calls = CallService(SqliteCallRepository(connection), CallAccessPolicy())
        ana = register_user(users, "ana", PASSWORD)
        luis = register_user(users, "luis", PASSWORD)
        maria = register_user(users, "maria", PASSWORD)
        with pytest.raises(ForbiddenError):
            calls.start(users, contacts, ana, "luis")
        add_contact(users, contacts, ana.id, "luis")
        call = calls.start(users, contacts, ana, "luis")
        with pytest.raises(ForbiddenError):
            calls.get_for(call.id.value, maria.id)
        calls.offer(call.id.value, ana.id, "offer", "v=0 oferta")
        calls.reject(call.id.value, luis.id)
        assert calls.get_for(call.id.value, luis.id).status is CallStatus.REJECTED
        with pytest.raises(CallConflictError):
            calls.offer(call.id.value, ana.id, "offer", "v=0 otra")


def test_senalizacion_ice(app):
    with get_connection(app.config["DATABASE"]) as connection:
        users = SqliteUserStore(connection)
        contacts = SqliteContactStore(connection)
        calls = CallService(SqliteCallRepository(connection), CallAccessPolicy())
        ana = register_user(users, "ana", PASSWORD)
        luis = register_user(users, "luis", PASSWORD)
        add_contact(users, contacts, ana.id, "luis")
        call = calls.start(users, contacts, ana, "luis")
        calls.offer(call.id.value, ana.id, "offer", "v=0 oferta")
        calls.answer(call.id.value, luis.id, "answer", "v=0 respuesta")
        ice = calls.add_ice(call.id.value, ana.id, "candidate:1", "0", 0)
        assert ice.record_id is not None
        pendientes = calls.list_ice(call.id.value, luis.id, 0)
        assert len(pendientes) == 1
        assert calls.list_ice(call.id.value, ana.id, 0) == []
        incoming = calls.incoming(luis.id)
        assert incoming == []
        calls.hang_up(call.id.value, luis.id)
        with pytest.raises(NotFoundError):
            calls.get_for("noexiste", ana.id)


def test_transiciones_invalidas():
    call = Call(CallId.generate(), Participant(1, "ana"), Participant(2, "luis"))
    with pytest.raises(ForbiddenError):
        call.place_offer(2, OFFER)
    with pytest.raises(CallConflictError):
        call.place_answer(2, ANSWER)
    call.place_offer(1, OFFER)
    with pytest.raises(CallConflictError):
        call.place_answer(2, OFFER)
    with pytest.raises(ForbiddenError):
        call.place_answer(1, ANSWER)
    with pytest.raises(ForbiddenError):
        call.reject(1)
    with pytest.raises(ForbiddenError):
        call.peer_of(9)
    with pytest.raises(ValidationError):
        Participant(1, "   ")
    with pytest.raises(ValidationError):
        IceCandidate("ok", None, None, 0)
    call.place_answer(2, ANSWER)
    with pytest.raises(CallConflictError):
        call.reject(2)

