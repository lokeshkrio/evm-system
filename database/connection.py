# database/connection.py

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aiosqlite


class DBConnection:
    """
    Manages an asynchronous SQLite connection lifecycle.
    """

    def __init__(self, db_path: str) -> None:

        self.db_path = db_path
        self.connection: aiosqlite.Connection | None = None
        self._transaction_lock = asyncio.Lock()

    async def connect(self) -> None:

        if self.connection is not None:
            return

        self.connection = await aiosqlite.connect(self.db_path)

        self.connection.row_factory = aiosqlite.Row

        await self.connection.execute("PRAGMA journal_mode=WAL")

        await self.connection.execute("PRAGMA foreign_keys=ON")

        await self.connection.commit()

    async def close(self) -> None:

        if self.connection is None:
            return

        await self.connection.close()

        self.connection = None

    async def execute(
        self,
        query: str,
        parameters: tuple = (),
    ) -> aiosqlite.Cursor:

        assert self.connection is not None

        return await self.connection.execute(
            query,
            parameters,
        )

    async def executemany(
        self,
        query: str,
        parameters: list[tuple],
    ) -> aiosqlite.Cursor:

        assert self.connection is not None

        return await self.connection.executemany(
            query,
            parameters,
        )

    async def fetchone(
        self,
        query: str,
        parameters: tuple = (),
    ):

        cursor = await self.execute(
            query,
            parameters,
        )

        return await cursor.fetchone()

    async def fetchall(
        self,
        query: str,
        parameters: tuple = (),
    ):

        cursor = await self.execute(
            query,
            parameters,
        )

        return await cursor.fetchall()

    async def commit(self) -> None:

        assert self.connection is not None

        await self.connection.commit()

    async def rollback(self) -> None:

        assert self.connection is not None

        await self.connection.rollback()

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        """Run a group of repository operations as one SQLite transaction."""
        if self.connection is None:
            raise RuntimeError("Database connection not established")

        async with self._transaction_lock:
            await self.connection.execute("BEGIN IMMEDIATE")
            try:
                yield
            except BaseException:
                await self.connection.rollback()
                raise
            else:
                await self.connection.commit()

    async def __aenter__(self):

        await self.connect()

        return self

    async def __aexit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):

        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

        await self.close()
