from __future__ import annotations

from app.domain.errors import ValidationError

ALLOWED_SDP_TYPES = {"offer", "answer"}
MAX_SDP_LENGTH = 100000
MAX_CANDIDATE_LENGTH = 4000


def sdp_lines(sdp: str) -> list[str]:
    unified = sdp.replace("\r\n", "\n").replace("\r", "\n")
    return [line.rstrip() for line in unified.split("\n") if line.strip()]


def join_sdp(lines: list[str]) -> str:
    return "\r\n".join(lines) + "\r\n"


class SessionDescription:
    def __init__(self, kind: str, sdp: str) -> None:
        if kind not in ALLOWED_SDP_TYPES:
            raise ValidationError("Tipo SDP no permitido.")
        text = join_sdp(sdp_lines(sdp))
        if text == "\r\n" or len(text) > MAX_SDP_LENGTH:
            raise ValidationError("SDP inválido.")
        self._kind = kind
        self._sdp = text

    @classmethod
    def from_payload(cls, kind: str, sdp: str, lines: list[str] | None = None) -> SessionDescription:
        if lines:
            return cls(kind, join_sdp([str(item) for item in lines]))
        return cls(kind, sdp)

    @property
    def kind(self) -> str:
        return self._kind

    @property
    def sdp(self) -> str:
        return self._sdp

    def to_dict(self) -> dict:
        return {
            "type": self._kind,
            "sdp": self._sdp,
            "lines": sdp_lines(self._sdp),
        }


class IceCandidate:
    def __init__(
        self,
        candidate: str,
        sdp_mid: str | None,
        sdp_m_line_index: int | None,
        sender_id: int,
        record_id: int | None = None,
    ) -> None:
        text = candidate.strip()
        if not text or len(text) > MAX_CANDIDATE_LENGTH:
            raise ValidationError("Candidato ICE inválido.")
        if sender_id < 1:
            raise ValidationError("Remitente ICE inválido.")
        self._candidate = text
        self._sdp_mid = sdp_mid
        self._sdp_m_line_index = sdp_m_line_index
        self._sender_id = sender_id
        self._record_id = record_id

    @property
    def candidate(self) -> str:
        return self._candidate

    @property
    def sdp_mid(self) -> str | None:
        return self._sdp_mid

    @property
    def sdp_m_line_index(self) -> int | None:
        return self._sdp_m_line_index

    @property
    def sender_id(self) -> int:
        return self._sender_id

    @property
    def record_id(self) -> int | None:
        return self._record_id

    def to_dict(self) -> dict:
        return {
            "id": self._record_id,
            "candidate": self._candidate,
            "sdpMid": self._sdp_mid,
            "sdpMLineIndex": self._sdp_m_line_index,
            "sender_id": self._sender_id,
        }
