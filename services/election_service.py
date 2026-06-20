import asyncio
import json
import logging
import sqlite3
from datetime import UTC, datetime
from typing import Any

from models.enums import ElectionState
from models.vote import Vote
from repositories.candidate_repository import CandidateRepository
from repositories.event_repository import EventRepository
from repositories.metadata_repository import MetadataRepository
from repositories.vote_repository import VoteRepository
from services.audit_service import AuditEvent, AuditService
from services.state_machine import ElectionStateMachine

logger = logging.getLogger(__name__)


class ElectionService:
    """Coordinates election rules without owning SQL or transport concerns."""

    def __init__(
        self,
        vote_repository: VoteRepository,
        candidate_repository: CandidateRepository,
        metadata_repository: MetadataRepository,
        event_repository: EventRepository,
        audit_service: AuditService,
        state_machine: ElectionStateMachine,
    ) -> None:
        self.vote_repository = vote_repository
        self.candidate_repository = candidate_repository
        self.metadata_repository = metadata_repository
        self.event_repository = event_repository
        self.audit = audit_service
        self.state = state_machine
        self.db = vote_repository.db

        repositories = (
            candidate_repository,
            metadata_repository,
            event_repository,
        )
        if any(repository.db is not self.db for repository in repositories):
            raise ValueError("Election repositories must share one DBConnection")

        # State transitions and vote writes form one serialized mutation stream.
        self._mutation_lock = asyncio.Lock()

    @property
    def can_vote(self) -> bool:
        return self.state.state == ElectionState.VOTING

    async def initialize(self) -> None:
        """Restore durable state and recover an interrupted voting session."""
        async with self._mutation_lock:
            persisted = await self.metadata_repository.get("election_state")
            if persisted is None:
                await self.metadata_repository.set(
                    "election_state",
                    ElectionState.INITIALIZED.value,
                )
                return

            try:
                restored_state = ElectionState(persisted)
            except ValueError as exc:
                raise RuntimeError(
                    f"Invalid persisted election state: {persisted!r}"
                ) from exc

            if restored_state == ElectionState.VOTING:
                restored_state = ElectionState.STARTED
                details = {
                    "from_state": ElectionState.VOTING.value,
                    "to_state": restored_state.value,
                    "reason": "server_restart",
                }
                async with self.db.transaction():
                    await self.metadata_repository.set(
                        "election_state",
                        restored_state.value,
                        commit=False,
                    )
                    await self._append_db_event(
                        AuditEvent.ELECTION_RECOVERED,
                        details,
                    )
                await self._write_file_audit(AuditEvent.ELECTION_RECOVERED, details)

            self.state.restore(restored_state)

    async def get_state(self) -> dict[str, str]:
        return {"state": self.state.state.value}

    async def get_status(self) -> dict[str, str | bool]:
        return {
            "state": self.state.state.value,
            "can_vote": self.can_vote,
        }

    async def start_election(self) -> dict[str, Any]:
        async with self._mutation_lock:
            old_state = self.state.state
            if not self.state.start_election():
                return {"success": False, "reason": "Election already started"}

            details = {"state": self.state.state.value}
            try:
                await self._persist_state_event(AuditEvent.ELECTION_STARTED, details)
            except BaseException:
                self.state.restore(old_state)
                raise

            await self._write_file_audit(AuditEvent.ELECTION_STARTED, details)
            return {"success": True, "state": self.state.state.value}

    async def enable_vote(self) -> dict[str, Any]:
        async with self._mutation_lock:
            old_state = self.state.state
            if not self.state.enable_vote():
                return {"success": False, "reason": "Cannot enable voting"}

            details = {"state": self.state.state.value}
            try:
                await self._persist_state_event(AuditEvent.VOTING_ENABLED, details)
            except BaseException:
                self.state.restore(old_state)
                raise

            await self._write_file_audit(AuditEvent.VOTING_ENABLED, details)
            return {"success": True, "state": self.state.state.value}

    async def halt_election(self) -> dict[str, Any]:
        async with self._mutation_lock:
            old_state = self.state.state
            if not self.state.halt():
                return {"success": False, "reason": "Cannot halt election"}

            details = {"state": self.state.state.value}
            try:
                await self._persist_state_event(AuditEvent.ELECTION_HALTED, details)
            except BaseException:
                self.state.restore(old_state)
                raise

            await self._write_file_audit(AuditEvent.ELECTION_HALTED, details)
            return {"success": True, "state": self.state.state.value}

    async def resume_election(self) -> dict[str, Any]:
        async with self._mutation_lock:
            old_state = self.state.state
            if not self.state.resume():
                return {"success": False, "reason": "Cannot resume election"}

            details = {"state": self.state.state.value}
            try:
                await self._persist_state_event(AuditEvent.ELECTION_RESUMED, details)
            except BaseException:
                self.state.restore(old_state)
                raise

            await self._write_file_audit(AuditEvent.ELECTION_RESUMED, details)
            return {"success": True, "state": self.state.state.value}

    async def stop_election(self) -> dict[str, Any]:
        async with self._mutation_lock:
            old_state = self.state.state
            if not self.state.end():
                return {"success": False, "reason": "Cannot stop election"}

            details = {"state": self.state.state.value}
            try:
                await self._persist_state_event(AuditEvent.ELECTION_STOPPED, details)
            except BaseException:
                self.state.restore(old_state)
                raise

            await self._write_file_audit(AuditEvent.ELECTION_STOPPED, details)
            return {"success": True, "state": self.state.state.value}

    async def cast_vote(
        self,
        voter_hash: str,
        candidate_id: int,
    ) -> dict[str, Any]:
        async with self._mutation_lock:
            if not self.can_vote:
                return {"success": False, "reason": "Voting disabled"}

            if not await self.candidate_repository.is_exists(candidate_id):
                return {"success": False, "reason": "Invalid or inactive candidate"}

            if await self.vote_repository.has_voted(voter_hash):
                await self._record_duplicate_attempt()
                return {"success": False, "reason": "Duplicate vote"}

            timestamp = datetime.now(UTC).isoformat()
            vote = Vote(
                voter_hash=voter_hash,
                candidate_id=candidate_id,
                timestamp=timestamp,
            )
            details = {"candidate_id": candidate_id}
            old_state = self.state.state

            try:
                async with self.db.transaction():
                    await self.vote_repository.record_vote(vote, commit=False)
                    if not self.state.vote_casted():
                        raise RuntimeError("Voting state changed during vote processing")
                    await self.metadata_repository.set(
                        "election_state",
                        self.state.state.value,
                        commit=False,
                    )
                    await self._append_db_event(
                        AuditEvent.VOTE_CAST,
                        details,
                        timestamp=timestamp,
                    )
            except sqlite3.IntegrityError as exc:
                self.state.restore(old_state)
                if "votes.voter_hash" not in str(exc):
                    raise
                await self._record_duplicate_attempt()
                return {"success": False, "reason": "Duplicate vote"}
            except BaseException:
                self.state.restore(old_state)
                raise

            await self._write_file_audit(AuditEvent.VOTE_CAST, details)
            return {"success": True}

    async def get_results(self) -> dict[str, Any]:
        if self.state.state != ElectionState.ENDED:
            return {
                "success": False,
                "reason": "Results are available only after the election ends",
            }

        return {
            "success": True,
            "results": await self.vote_repository.get_results(),
        }

    async def _persist_state_event(
        self,
        event: AuditEvent,
        details: dict[str, Any],
    ) -> None:
        async with self.db.transaction():
            await self.metadata_repository.set(
                "election_state",
                self.state.state.value,
                commit=False,
            )
            await self._append_db_event(event, details)

    async def _append_db_event(
        self,
        event: AuditEvent,
        details: dict[str, Any],
        *,
        timestamp: str | None = None,
    ) -> None:
        await self.event_repository.append_event(
            event.value,
            json.dumps(details, sort_keys=True, separators=(",", ":")),
            timestamp or datetime.now(UTC).isoformat(),
            commit=False,
        )

    async def _record_duplicate_attempt(self) -> None:
        details = {"reason": "voter_already_recorded"}
        async with self.db.transaction():
            await self._append_db_event(AuditEvent.DUPLICATE_VOTE, details)
        await self._write_file_audit(AuditEvent.DUPLICATE_VOTE, details)

    async def _write_file_audit(
        self,
        event: AuditEvent,
        details: dict[str, Any],
    ) -> None:
        try:
            await self.audit.log_event(event, details)
        except Exception:
            # The database event is authoritative; a secondary sink must not
            # turn an already committed operation into a reported failure.
            logger.exception("Failed to append event to JSONL audit ledger")
