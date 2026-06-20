from dataclasses import dataclass


@dataclass(slots=True)
class Metadata:
    """Stores the global system metadata of the current election.

    Attributes:
        state: The current state of the election (e.g., 'INITIALIZED', 'STARTED').
        total_votes: Total number of votes cast in this election so far.
    """
    state: str
    total_votes: int
