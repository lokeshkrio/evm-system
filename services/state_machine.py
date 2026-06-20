from database.unit_of_work import UnitOfWork
from models.enums import ElectionState


class PersistentElectionStateMachine:
    """State machine that manages election lifecycle directly via the database repository."""

    async def get_state(self, uow: UnitOfWork) -> ElectionState:
        persisted = await uow.metadata.get("election_state")
        if persisted is None:
            return ElectionState.INITIALIZED
        try:
            return ElectionState(persisted)
        except ValueError as exc:
            raise RuntimeError(f"Invalid persisted election state: {persisted!r}") from exc

    async def _transition(self, uow: UnitOfWork, next_state: ElectionState) -> ElectionState:
        await uow.metadata.set("election_state", next_state.value)
        return next_state

    async def start_election(self, uow: UnitOfWork) -> ElectionState | None:
        current = await self.get_state(uow)
        if current != ElectionState.INITIALIZED:
            return None
        return await self._transition(uow, ElectionState.STARTED)

    async def enable_vote(self, uow: UnitOfWork) -> ElectionState | None:
        current = await self.get_state(uow)
        if current != ElectionState.STARTED:
            return None
        return await self._transition(uow, ElectionState.VOTING)

    async def vote_casted(self, uow: UnitOfWork) -> ElectionState | None:
        current = await self.get_state(uow)
        if current != ElectionState.VOTING:
            return None
        return await self._transition(uow, ElectionState.STARTED)

    async def halt(self, uow: UnitOfWork) -> ElectionState | None:
        current = await self.get_state(uow)
        if current != ElectionState.VOTING:
            return None
        return await self._transition(uow, ElectionState.HALTED)

    async def resume(self, uow: UnitOfWork) -> ElectionState | None:
        current = await self.get_state(uow)
        if current != ElectionState.HALTED:
            return None
        return await self._transition(uow, ElectionState.STARTED)

    async def end(self, uow: UnitOfWork) -> ElectionState | None:
        current = await self.get_state(uow)
        if current not in (ElectionState.STARTED, ElectionState.HALTED):
            return None
        return await self._transition(uow, ElectionState.ENDED)

    async def reset(self, uow: UnitOfWork) -> ElectionState | None:
        current = await self.get_state(uow)
        if current != ElectionState.ENDED:
            return None
        return await self._transition(uow, ElectionState.INITIALIZED)
