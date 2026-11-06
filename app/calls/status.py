from enum import Enum


class CallStatus(str, Enum):
    RINGING = "ringing"
    OFFERING = "offering"
    IN_CALL = "in_call"
    ENDED = "ended"
    REJECTED = "rejected"

    def is_open(self) -> bool:
        return self in {CallStatus.RINGING, CallStatus.OFFERING, CallStatus.IN_CALL}
