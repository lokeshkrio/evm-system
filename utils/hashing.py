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
    serialized_event = json.dumps({
        "event_type": event_type,
        "payload": payload,
        "timestamp": timestamp,
    }, sort_keys=True, separators=(",", ":"))
    content = previous_hash + serialized_event
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
