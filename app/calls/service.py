from __future__ import annotations

from app.calls.identity import CallId, Participant
from app.calls.model import Call
from app.calls.policy import CallAccessPolicy
from app.calls.ports import CallRepository
from app.calls.signaling import IceCandidate, SessionDescription
from app.domain.errors import NotFoundError
from app.domain.records import UserRecord
from app.persistence.repositories import ContactStore, UserStore
from app.domain.validation import validate_username


class CallService:
    def __init__(self, repository: CallRepository, policy: CallAccessPolicy) -> None:
        self._repository = repository
        self._policy = policy

    def start(
        self,
        users: UserStore,
        contacts: ContactStore,
        caller: UserRecord,
        callee_username: str,
    ) -> Call:
        username = validate_username(callee_username)
        callee = users.find_by_username(username)
        if callee is None:
            raise NotFoundError("El destinatario no existe.")
        self._policy.ensure_can_call(contacts, caller.id, callee.id)
        call = Call(
            CallId.generate(),
            Participant(caller.id, caller.username),
            Participant(callee.id, callee.username),
        )
        self._repository.add(call)
        return call

    def incoming(self, user_id: int) -> list[Call]:
        return self._repository.incoming_for(user_id)

    def get_for(self, call_id: str, user_id: int) -> Call:
        call = self._require(call_id)
        self._policy.ensure_member(call, user_id)
        return call

    def offer(
        self,
        call_id: str,
        user_id: int,
        kind: str,
        sdp: str,
        lines: list[str] | None = None,
    ) -> Call:
        call = self.get_for(call_id, user_id)
        call.place_offer(user_id, SessionDescription.from_payload(kind, sdp, lines))
        self._repository.save(call)
        return call

    def answer(
        self,
        call_id: str,
        user_id: int,
        kind: str,
        sdp: str,
        lines: list[str] | None = None,
    ) -> Call:
        call = self.get_for(call_id, user_id)
        call.place_answer(user_id, SessionDescription.from_payload(kind, sdp, lines))
        self._repository.save(call)
        return call

    def hang_up(self, call_id: str, user_id: int) -> Call:
        call = self.get_for(call_id, user_id)
        call.hang_up(user_id)
        self._repository.save(call)
        return call

    def reject(self, call_id: str, user_id: int) -> Call:
        call = self.get_for(call_id, user_id)
        call.reject(user_id)
        self._repository.save(call)
        return call

    def add_ice(
        self,
        call_id: str,
        user_id: int,
        candidate: str,
        sdp_mid: str | None,
        sdp_m_line_index: int | None,
    ) -> IceCandidate:
        call = self.get_for(call_id, user_id)
        ice = IceCandidate(candidate, sdp_mid, sdp_m_line_index, user_id)
        return self._repository.add_ice(call.id, ice)

    def list_ice(self, call_id: str, user_id: int, after_id: int) -> list[IceCandidate]:
        call = self.get_for(call_id, user_id)
        return self._repository.ice_after(call.id, after_id, user_id)

    def _require(self, call_id: str) -> Call:
        found = self._repository.get(CallId(call_id))
        if found is None:
            raise NotFoundError("La llamada no existe.")
        return found
