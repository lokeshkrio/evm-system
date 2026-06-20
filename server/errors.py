class ElectionError(Exception):
    """Base class for all exceptions related to the election logic."""
    pass


class ElectionAlreadyStartedError(ElectionError):
    """Raised when attempting to start an election that is already in progress."""
    pass


class ElectionEndedError(ElectionError):
    """Raised when performing operations on an election that has already ended."""
    pass


class ElectionNotStartedError(ElectionError):
    """Raised when performing operations (like voting) before the election starts."""
    pass


class DuplicateVoteError(ElectionError):
    """Raised when a voter attempts to cast a vote more than once."""
    pass


class CandidateNotFoundError(ElectionError):
    """Raised when a vote is cast for a candidate that does not exist or is inactive."""
    pass