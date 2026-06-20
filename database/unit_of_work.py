from contextlib import AbstractAsyncContextManager
from types import TracebackType

from database.connection import DBConnection
from repositories.candidate_repository import CandidateRepository
from repositories.event_repository import EventRepository
from repositories.metadata_repository import MetadataRepository
from repositories.vote_repository import VoteRepository


class UnitOfWork:
    """Owns one transaction and the repositories participating in it."""

    def __init__(self, db: DBConnection) -> None:
        self.db = db
        self.votes = VoteRepository(db)
        self.candidates = CandidateRepository(db)
        self.metadata = MetadataRepository(db)
        self.events = EventRepository(db)
        self._transaction: AbstractAsyncContextManager[None] | None = None

    async def __aenter__(self) -> "UnitOfWork":
        self._transaction = self.db.transaction()
        await self._transaction.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        if self._transaction is None:
            raise RuntimeError("UnitOfWork was not entered")
        try:
            return await self._transaction.__aexit__(exc_type, exc_value, traceback)
        finally:
            self._transaction = None
