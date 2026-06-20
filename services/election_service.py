from models.enums import ElectionState
from services.audit_service import AuditEvent


class ElectionService:
    """Service coordinating the election lifecycle and auditing state transitions."""

    def __init__(
        self,
        vote_repository,
        candidate_repository,
        metadata_repository,
        event_repository,
        audit_service,
        state_machine,
    ):

        self.vote_repository = vote_repository
        self.candidate_repository = candidate_repository
        self.metadata_repository = metadata_repository
        self.event_repository = event_repository

        self.audit = audit_service
        self.state = state_machine

    @property
    def can_vote(self) -> bool:
        """Checks if the election is in the VOTING state.

        Returns:
            True if voting is allowed, False otherwise.
        """
        return self.state.state == ElectionState.VOTING

    async def get_state(self):

        return {"state": self.state.state.value}

    async def get_status(self):

        return {"can_vote": self.can_vote}

    async def start_election(self) -> dict:

        self.state.advance_state()

        await self.metadata_repository.set("election_state", self.state.state.value)

        await self.audit.log_event(
            AuditEvent.ELECTION_STARTED, {"state": self.state.state.value}
        )

        return {"success": True, "state": self.state.state.value}

    async def stop_election(self) -> dict:

        if not self.state.end():

            return {"success": False}

        await self.metadata_repository.set("election_state", self.state.state.value)

        await self.audit.log_event(
            AuditEvent.ELECTION_STOPPED, {"state": self.state.state.value}
        )

        return {"success": True, "state": self.state.state.value}

    async def halt_election(self) -> dict:

        if not self.state.halt():

            return {"success": False}

        await self.metadata_repository.set("election_state", self.state.state.value)

        await self.audit.log_event(
            AuditEvent.ELECTION_HALTED, {"state": self.state.state.value}
        )

        return {"success": True, "state": self.state.state.value}

    async def cast_vote(
        self,
        voter_hash: str,
        candidate_id: int,
    ):

        if not self.can_vote:

            return {"success": False, "reason": "Voting disabled"}

        if not await self.candidate_repository.is_exists(candidate_id):

            return {"success": False, "reason": "Invalid candidate"}

        if await self.vote_repository.has_voted(voter_hash):

            await self.audit.log_event(
                AuditEvent.DUPLICATE_VOTE, {"voter_hash": voter_hash}
            )

            return {"success": False, "reason": "Duplicate vote"}

        from datetime import UTC, datetime
        from models.vote import Vote

        vote = Vote(
            voter_hash=voter_hash,
            candidate_id=candidate_id,
            timestamp=datetime.now(UTC).isoformat(),
        )

        await self.vote_repository.record_vote(vote)

        await self.audit.log_event(AuditEvent.VOTE_CAST, {"candidate_id": candidate_id})

        return {"success": True}

    async def get_results(self):

        results = await self.vote_repository.get_results()

        return {"results": results}
