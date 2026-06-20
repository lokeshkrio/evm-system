from enum import Enum


class ElectionState(Enum):
    """Enumeration of possible states in the election lifecycle."""

    INITIALIZED = "INITIALIZED"
    STARTED = "STARTED"
    VOTING = "VOTING"
    HALTED = "HALTED"
    ENDED = "ENDED"
