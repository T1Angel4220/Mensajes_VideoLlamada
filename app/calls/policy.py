from app.calls.model import Call
from app.domain.errors import ForbiddenError
from app.persistence.repositories import ContactStore


class CallAccessPolicy:
    def ensure_member(self, call: Call, user_id: int) -> None:
        if not call.has_participant(user_id):
            raise ForbiddenError("No participas en esta llamada.")

    def ensure_can_call(self, contacts: ContactStore, caller_id: int, callee_id: int) -> None:
        if not contacts.exists(caller_id, callee_id):
            raise ForbiddenError("Debes agregar al contacto antes de llamarlo.")
