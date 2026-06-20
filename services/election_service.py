import asyncio
import json
import sqlite3
from collections.abc import Callable
from typing import Any

from database.unit_of_work import UnitOfWork
from events.event_bus import EventBus
from events.event_types import (
    DomainEvent,
    DuplicateVoteEvent,
    ElectionHaltedEvent,
    ElectionRecoveredEvent,
    ElectionResumedEvent,
    ElectionStartedEvent,
    ElectionStoppedEvent,
    VoteCastEvent,
    VotingEnabledEvent,
)
from models.enums import ElectionState
from models.vote import Vote
from repositories.event_repository import EventRepository
from repositories.metadata_repository import MetadataRepository
from services.state_machine import ElectionStateMachine
from utils.hashing import GENESIS_EVENT_HASH, hash_database_event

UnitOfWorkFactory = Callable[[], UnitOfWork]


class ElectionService:
    """Coordinates durable election use cases and post-commit events."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        state_machine: ElectionStateMachine,
        event_bus: EventBus,
    ) -> None:
        self._new_unit_of_work = unit_of_work_factory
        self.state_machine = state_machine
        self.event_bus = event_bus
        self._mutation_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Verify event integrity and recover durable state after restart."""
        recovery_event: DomainEvent | None = None

        async with self._mutation_lock:
            async with self._new_unit_of_work() as uow:
                await self._verify_event_chain(uow.events)
                persisted = await uow.metadata.get("election_state")

                if persisted is None:
                    await uow.metadata.set(
                        "election_state",
                        ElectionState.INITIALIZED.value,
                    )
                else:
                    current = self._parse_state(persisted)
                    if current == ElectionState.VOTING:
                        recovery_event = ElectionRecoveredEvent(
                            {
                                "from_state": ElectionState.VOTING.value,
                                "to_state": ElectionState.STARTED.value,
                                "reason": "server_restart",
                            }
                        )
                        await uow.metadata.set(
                            "election_state",
                            ElectionState.STARTED.value,
                        )
                        await self._append_db_event(uow.events, recovery_event)

        if recovery_event is not None:
            await self.event_bus.publish(recovery_event)

    async def get_state(self) -> dict[str, str]:
        async with self._new_unit_of_work() as uow:
            state = await self._load_state(uow.metadata)
        return {"state": state.value}

    async def get_status(self) -> dict[str, str | bool]:
        async with self._new_unit_of_work() as uow:
            state = await self._load_state(uow.metadata)
        return {
            "state": state.value,
            "can_vote": state == ElectionState.VOTING,
        }

    async def start_election(self) -> dict[str, Any]:
        event: DomainEvent | None = None
        async with self._mutation_lock:
            async with self._new_unit_of_work() as uow:
                current = await self._load_state(uow.metadata)
                next_state = self.state_machine.start_election(current)
                if next_state is None:
                    result = {"success": False, "reason": "Election already started"}
                else:
                    event = ElectionStartedEvent({"state": next_state.value})
                    await uow.metadata.set("election_state", next_state.value)
                    await self._append_db_event(uow.events, event)
                    result = {"success": True, "state": next_state.value}

        if event is not None:
            await self.event_bus.publish(event)
        return result

    async def enable_vote(self) -> dict[str, Any]:
        event: DomainEvent | None = None
        async with self._mutation_lock:
            async with self._new_unit_of_work() as uow:
                current = await self._load_state(uow.metadata)
                next_state = self.state_machine.enable_vote(current)
                if next_state is None:
                    result = {"success": False, "reason": "Cannot enable voting"}
                else:
                    event = VotingEnabledEvent({"state": next_state.value})
                    await uow.metadata.set("election_state", next_state.value)
                    await self._append_db_event(uow.events, event)
                    result = {"success": True, "state": next_state.value}

        if event is not None:
            await self.event_bus.publish(event)
        return result

    async def halt_election(self) -> dict[str, Any]:
        event: DomainEvent | None = None
        async with self._mutation_lock:
            async with self._new_unit_of_work() as uow:
                current = await self._load_state(uow.metadata)
                next_state = self.state_machine.halt(current)
                if next_state is None:
                    result = {"success": False, "reason": "Cannot halt election"}
                else:
                    event = ElectionHaltedEvent({"state": next_state.value})
                    await uow.metadata.set("election_state", next_state.value)
                    await self._append_db_event(uow.events, event)
                    result = {"success": True, "state": next_state.value}

        if event is not None:
            await self.event_bus.publish(event)
        return result

    async def resume_election(self) -> dict[str, Any]:
        event: DomainEvent | None = None
        async with self._mutation_lock:
            async with self._new_unit_of_work() as uow:
                current = await self._load_state(uow.metadata)
                next_state = self.state_machine.resume(current)
                if next_state is None:
                    result = {"success": False, "reason": "Cannot resume election"}
                else:
                    event = ElectionResumedEvent({"state": next_state.value})
                    await uow.metadata.set("election_state", next_state.value)
                    await self._append_db_event(uow.events, event)
                    result = {"success": True, "state": next_state.value}

        if event is not None:
            await self.event_bus.publish(event)
        return result

    async def stop_election(self) -> dict[str, Any]:
        event: DomainEvent | None = None
        async with self._mutation_lock:
            async with self._new_unit_of_work() as uow:
                current = await self._load_state(uow.metadata)
                next_state = self.state_machine.end(current)
                if next_state is None:
                    result = {"success": False, "reason": "Cannot stop election"}
                else:
                    event = ElectionStoppedEvent({"state": next_state.value})
                    await uow.metadata.set("election_state", next_state.value)
                    await self._append_db_event(uow.events, event)
                    result = {"success": True, "state": next_state.value}

        if event is not None:
            await self.event_bus.publish(event)
        return result

    async def cast_vote(
        self,
        voter_hash: str,
        candidate_id: int,
    ) -> dict[str, Any]:
        event: DomainEvent | None = None

        async with self._mutation_lock:
            try:
                async with self._new_unit_of_work() as uow:
                    current = await self._load_state(uow.metadata)
                    if current != ElectionState.VOTING:
                        result = {"success": False, "reason": "Voting disabled"}
                    elif not await uow.candidates.is_exists(candidate_id):
                        result = {
                            "success": False,
                            "reason": "Invalid or inactive candidate",
                        }
                    elif await uow.votes.has_voted(voter_hash):
                        event = DuplicateVoteEvent(
                            {"reason": "voter_already_recorded"}
                        )
                        await self._append_db_event(uow.events, event)
                        result = {"success": False, "reason": "Duplicate vote"}
                    else:
                        next_state = self.state_machine.vote_casted(current)
                        if next_state is None:
                            raise RuntimeError("Voting state transition was rejected")

                        event = VoteCastEvent({"candidate_id": candidate_id})
                        vote = Vote(
                            voter_hash=voter_hash,
                            candidate_id=candidate_id,
                            timestamp=event.timestamp,
                        )
                        await uow.votes.record_vote(vote)
                        await uow.metadata.set("election_state", next_state.value)
                        await self._append_db_event(uow.events, event)
                        result = {"success": True}
            except sqlite3.IntegrityError as exc:
                if "votes.voter_hash" not in str(exc):
                    raise
                event = await self._record_duplicate_attempt()
                result = {"success": False, "reason": "Duplicate vote"}

        if event is not None:
            await self.event_bus.publish(event)
        return result

    async def get_results(self) -> dict[str, Any]:
        async with self._new_unit_of_work() as uow:
            state = await self._load_state(uow.metadata)
            if state != ElectionState.ENDED:
                return {
                    "success": False,
                    "reason": "Results are available only after the election ends",
                }
            results = await uow.votes.get_results()

        return {"success": True, "results": results}

    async def _record_duplicate_attempt(self) -> DomainEvent:
        event = DuplicateVoteEvent({"reason": "voter_already_recorded"})
        async with self._new_unit_of_work() as uow:
            await self._append_db_event(uow.events, event)
        return event

    async def _append_db_event(
        self,
        repository: EventRepository,
        event: DomainEvent,
    ) -> None:
        payload = json.dumps(event.details, sort_keys=True, separators=(",", ":"))
        previous_hash = await repository.get_last_hash() or GENESIS_EVENT_HASH
        event_hash = hash_database_event(
            previous_hash,
            event.event_type,
            payload,
            event.timestamp,
        )
        await repository.append_event(
            event.event_type,
            payload,
            event.timestamp,
            previous_hash,
            event_hash,
        )

    async def _verify_event_chain(self, repository: EventRepository) -> None:
        previous_hash = GENESIS_EVENT_HASH
        for event in await repository.list_events():
            computed_hash = hash_database_event(
                previous_hash,
                str(event["event_type"]),
                str(event["payload"]),
                str(event["timestamp"]),
            )
            if event["previous_hash"] != previous_hash:
                raise RuntimeError("Database event chain has a broken link")
            if event["event_hash"] != computed_hash:
                raise RuntimeError("Database event chain integrity check failed")
            previous_hash = computed_hash

    async def _load_state(
        self,
        repository: MetadataRepository,
    ) -> ElectionState:
        persisted = await repository.get("election_state")
        if persisted is None:
            raise RuntimeError("Election state is not initialized")
        return self._parse_state(persisted)

    @staticmethod
    def _parse_state(value: str) -> ElectionState:
        try:
            return ElectionState(value)
        except ValueError as exc:
            raise RuntimeError(f"Invalid persisted election state: {value!r}") from exc
