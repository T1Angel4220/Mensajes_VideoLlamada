from __future__ import annotations

from typing import Protocol

from app.calls.identity import CallId
from app.calls.model import Call
from app.calls.signaling import IceCandidate


class CallRepository(Protocol):
    def add(self, call: Call) -> None: ...

    def get(self, call_id: CallId) -> Call | None: ...

    def save(self, call: Call) -> None: ...

    def incoming_for(self, user_id: int) -> list[Call]: ...

    def add_ice(self, call_id: CallId, candidate: IceCandidate) -> IceCandidate: ...

    def ice_after(self, call_id: CallId, after_id: int, viewer_id: int) -> list[IceCandidate]: ...
