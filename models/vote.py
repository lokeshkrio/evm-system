from dataclasses import dataclass


@dataclass(slots=True)
class Vote:
    """Represents a cast vote in the system.

    Attributes:
        voter_hash: The cryptographic hash of the voter's ID to preserve anonymity.
        candidate_id: The ID of the candidate voted for.
        timestamp: ISO 8601 formatted timestamp of when the vote was cast.
    """
    voter_hash: str
    candidate_id: int
    timestamp: str
