import hashlib
import json
from typing import Any


GENESIS_EVENT_HASH = hashlib.sha256(b"evm_database_event_genesis").hexdigest()


def hash_voter_id(voter_id: str) -> str:
    """Generates a secure SHA-256 cryptographic hash of the voter ID."""
    return hashlib.sha256(voter_id.encode("utf-8")).hexdigest()


def hash_database_event(
    previous_hash: str,
    event_type: str,
    payload: str,
    timestamp: str,
) -> str:
    """Hash a canonical event envelope and its predecessor."""
    envelope: dict[str, Any] = {
        "event_type": event_type,
        "payload": payload,
        "previous_hash": previous_hash,
        "timestamp": timestamp,
    }
    canonical = json.dumps(envelope, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
