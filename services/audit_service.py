# services/audit_service.py

import asyncio
import hashlib
import json
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class AuditEvent(Enum):
    """Enumeration of possible events to be recorded in the audit ledger."""
    ELECTION_STARTED = "ELECTION_STARTED"
    ELECTION_STOPPED = "ELECTION_STOPPED"
    ELECTION_HALTED = "ELECTION_HALTED"

    VOTE_CAST = "VOTE_CAST"
    DUPLICATE_VOTE = "DUPLICATE_VOTE"

    CLIENT_CONNECTED = "CLIENT_CONNECTED"
    CLIENT_DISCONNECTED = "CLIENT_DISCONNECTED"

    INVALID_RPC_REQUEST = "INVALID_RPC_REQUEST"
    RPC_ERROR = "RPC_ERROR"

    RESULT_GENERATED = "RESULT_GENERATED"


class AuditService:
    """Tamper-evident append-only audit ledger.

    Each entry stores:
        - sequence number
        - timestamp
        - action
        - details
        - previous hash
        - current hash

    The chain can later be verified to detect modifications.
    """

    GENESIS_HASH = hashlib.sha256(b"genesis_block").hexdigest()

    def __init__(
        self,
        log_path: str = "logs/audit_ledger.jsonl",
    ) -> None:
        """Initializes the AuditService and ensures the log directory exists.

        Args:
            log_path: The file path to write the JSON lines audit ledger.
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._lock = asyncio.Lock()
        self._last_hash = self._get_tail_hash()
        self._sequence_number = self._get_last_sequence()

    def _get_tail_hash(self) -> str:
        """Retrieves the hash of the last entry in the ledger, or the genesis hash.

        Returns:
            The SHA-256 hash string of the tail entry.
        """
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            return self.GENESIS_HASH

        with self.log_path.open("r", encoding="utf-8") as file:
            lines = file.readlines()
            if not lines:
                return self.GENESIS_HASH

            last_entry = json.loads(lines[-1])
            return last_entry["hash"]

    def _get_last_sequence(self) -> int:
        """Gets the sequence number of the last entry in the ledger.

        Returns:
            The last sequence number as an integer.
        """
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            return 0

        with self.log_path.open("r", encoding="utf-8") as file:
            lines = file.readlines()
            if not lines:
                return 0
            last_entry = json.loads(lines[-1])
            return last_entry["sequence_number"]

    async def log_event(
        self,
        action: AuditEvent,
        details: dict[str, Any],
    ) -> dict[str, Any]:
        """Locks, computes SHA-256 hash chain link, and appends a new event to the ledger.

        Args:
            action: The AuditEvent enum representing the action.
            details: Extra metadata context related to the event.

        Returns:
            A dictionary containing the logged entry structure.
        """
        async with self._lock:
            timestamp = datetime.now(UTC).isoformat()
            sequence_number = self._sequence_number + 1
            payload = (
                f"{sequence_number}"
                f"{timestamp}"
                f"{action.value}"
                f"{json.dumps(details, sort_keys=True)}"
                f"{self._last_hash}"
            )

            current_hash = hashlib.sha256(payload.encode()).hexdigest()

            entry = {
                "sequence_number": sequence_number,
                "timestamp": timestamp,
                "action": action.value,
                "details": details,
                "previous_hash": self._last_hash,
                "hash": current_hash,
            }

            with self.log_path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(entry) + "\n")

            self._last_hash = current_hash
            self._sequence_number = sequence_number

            return entry

    def verify_chain(self) -> bool:
        """Verifies that the entire ledger sequence and hash integrity are unbroken.

        Returns:
            True if the ledger is valid and untampered, False if there is a mismatch.
        """
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            return True

        previous_hash = self.GENESIS_HASH

        with self.log_path.open("r", encoding="utf-8") as file:
            for line in file:
                entry = json.loads(line)

                payload = (
                    f"{entry['sequence_number']}"
                    f"{entry['timestamp']}"
                    f"{entry['action']}"
                    f"{json.dumps(entry['details'], sort_keys=True)}"
                    f"{entry['previous_hash']}"
                )

                computed_hash = hashlib.sha256(payload.encode()).hexdigest()

                if entry["previous_hash"] != previous_hash:
                    return False

                if entry["hash"] != computed_hash:
                    return False

                previous_hash = entry["hash"]

        return True
