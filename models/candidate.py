from dataclasses import dataclass


@dataclass(slots=True)
class Candidate:
    """Represents a political candidate in the election system.

    Attributes:
        candidate_id: A unique identifier for the candidate.
        name: The name of the candidate.
        party: The political party the candidate belongs to.
        active: A flag indicating if the candidate is currently active in the election.
    """
    candidate_id: int
    name: str
    party: str
    active: bool = True
