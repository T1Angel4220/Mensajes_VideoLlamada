from __future__ import annotations

import sqlite3

from app.calls.identity import CallId, Participant
from app.calls.model import Call
from app.calls.signaling import IceCandidate, SessionDescription
from app.calls.status import CallStatus


class SqliteCallRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, call: Call) -> None:
        self._connection.execute(
            """
            INSERT INTO calls (id, caller_id, callee_id, caller_name, callee_name, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                call.id.value,
                call.caller.user_id,
                call.callee.user_id,
                call.caller.username,
                call.callee.username,
                call.status.value,
            ),
        )

    def get(self, call_id: CallId) -> Call | None:
        row = self._connection.execute(
            "SELECT * FROM calls WHERE id = ?",
            (call_id.value,),
        ).fetchone()
        if row is None:
            return None
        return self._to_call(row)

    def save(self, call: Call) -> None:
        offer = call.offer
        answer = call.answer
        self._connection.execute(
            """
            UPDATE calls
            SET status = ?, offer_type = ?, offer_sdp = ?, answer_type = ?, answer_sdp = ?
            WHERE id = ?
            """,
            (
                call.status.value,
                None if offer is None else offer.kind,
                None if offer is None else offer.sdp,
                None if answer is None else answer.kind,
                None if answer is None else answer.sdp,
                call.id.value,
            ),
        )

    def incoming_for(self, user_id: int) -> list[Call]:
        rows = self._connection.execute(
            """
            SELECT * FROM calls
            WHERE callee_id = ? AND status IN ('ringing', 'offering')
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()
        return [self._to_call(row) for row in rows]

    def add_ice(self, call_id: CallId, candidate: IceCandidate) -> IceCandidate:
        cursor = self._connection.execute(
            """
            INSERT INTO ice_candidates
                (call_id, sender_id, candidate, sdp_mid, sdp_m_line_index)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                call_id.value,
                candidate.sender_id,
                candidate.candidate,
                candidate.sdp_mid,
                candidate.sdp_m_line_index,
            ),
        )
        return IceCandidate(
            candidate.candidate,
            candidate.sdp_mid,
            candidate.sdp_m_line_index,
            candidate.sender_id,
            cursor.lastrowid,
        )

    def ice_after(
        self, call_id: CallId, after_id: int, viewer_id: int
    ) -> list[IceCandidate]:
        rows = self._connection.execute(
            """
            SELECT id, sender_id, candidate, sdp_mid, sdp_m_line_index
            FROM ice_candidates
            WHERE call_id = ? AND id > ? AND sender_id != ?
            ORDER BY id ASC
            """,
            (call_id.value, after_id, viewer_id),
        ).fetchall()
        return [
            IceCandidate(
                row["candidate"],
                row["sdp_mid"],
                row["sdp_m_line_index"],
                row["sender_id"],
                row["id"],
            )
            for row in rows
        ]

    def _to_call(self, row: sqlite3.Row) -> Call:
        offer = None
        if row["offer_sdp"]:
            offer = SessionDescription(row["offer_type"], row["offer_sdp"])
        answer = None
        if row["answer_sdp"]:
            answer = SessionDescription(row["answer_type"], row["answer_sdp"])
        return Call(
            CallId(row["id"]),
            Participant(row["caller_id"], row["caller_name"]),
            Participant(row["callee_id"], row["callee_name"]),
            CallStatus(row["status"]),
            offer,
            answer,
        )
