import hashlib


def hash_voter_id(voter_id: str) -> str:
    """Generates a secure SHA-256 cryptographic hash of the voter ID."""
    return hashlib.sha256(voter_id.encode("utf-8")).hexdigest()
