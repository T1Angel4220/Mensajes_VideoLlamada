from __future__ import annotations

from app.calls.errors import CallConflictError
from app.calls.identity import CallId, Participant
from app.calls.signaling import SessionDescription
from app.calls.status import CallStatus
from app.domain.errors import ForbiddenError


class Call:
    def __init__(
        self,
        call_id: CallId,
        caller: Participant,
        callee: Participant,
        status: CallStatus = CallStatus.RINGING,
        offer: SessionDescription | None = None,
        answer: SessionDescription | None = None,
    ) -> None:
        if caller.user_id == callee.user_id:
            raise CallConflictError("La llamada debe ser entre dos personas.")
        self._id = call_id
        self._caller = caller
        self._callee = callee
        self._status = status
        self._offer = offer
        self._answer = answer

    @property
    def id(self) -> CallId:
        return self._id

    @property
    def caller(self) -> Participant:
        return self._caller

    @property
    def callee(self) -> Participant:
        return self._callee

    @property
    def status(self) -> CallStatus:
        return self._status

    @property
    def offer(self) -> SessionDescription | None:
        return self._offer

    @property
    def answer(self) -> SessionDescription | None:
        return self._answer

    def has_participant(self, user_id: int) -> bool:
        return user_id in {self._caller.user_id, self._callee.user_id}

    def peer_of(self, user_id: int) -> Participant:
        if user_id == self._caller.user_id:
            return self._callee
        if user_id == self._callee.user_id:
            return self._caller
        raise ForbiddenError("No participas en esta llamada.")

    def place_offer(self, actor_id: int, description: SessionDescription) -> None:
        self._ensure_open()
        if actor_id != self._caller.user_id:
            raise ForbiddenError("Solo quien llama puede enviar la oferta.")
        if description.kind != "offer":
            raise CallConflictError("Se esperaba una oferta SDP.")
        self._offer = description
        self._status = CallStatus.OFFERING

    def place_answer(self, actor_id: int, description: SessionDescription) -> None:
        self._ensure_open()
        if actor_id != self._callee.user_id:
            raise ForbiddenError("Solo el destinatario puede responder.")
        if self._offer is None:
            raise CallConflictError("Aún no hay oferta para responder.")
        if description.kind != "answer":
            raise CallConflictError("Se esperaba una respuesta SDP.")
        self._answer = description
        self._status = CallStatus.IN_CALL

    def hang_up(self, actor_id: int) -> None:
        if not self.has_participant(actor_id):
            raise ForbiddenError("No participas en esta llamada.")
        if not self._status.is_open():
            return
        self._status = CallStatus.ENDED

    def reject(self, actor_id: int) -> None:
        if actor_id != self._callee.user_id:
            raise ForbiddenError("Solo el destinatario puede rechazar.")
        if self._status not in {CallStatus.RINGING, CallStatus.OFFERING}:
            raise CallConflictError("La llamada ya no se puede rechazar.")
        self._status = CallStatus.REJECTED

    def _ensure_open(self) -> None:
        if not self._status.is_open():
            raise CallConflictError("La llamada ya está cerrada.")

    def to_dict(self, viewer_id: int) -> dict:
        peer = self.peer_of(viewer_id)
        return {
            "id": self._id.value,
            "status": self._status.value,
            "role": "caller" if viewer_id == self._caller.user_id else "callee",
            "peer": peer.username,
            "offer": None if self._offer is None else self._offer.to_dict(),
            "answer": None if self._answer is None else self._answer.to_dict(),
        }
