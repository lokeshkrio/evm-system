import aiosqlite


class DBConnection:
    """Manages an asynchronous SQLite database connection lifecycle.

    Attributes:
        db_path: The filesystem path to the SQLite database file.
        connection: The raw aiosqlite.Connection instance, or None if disconnected.
    """

    def __init__(self, db_path: str) -> None:
        """Initializes the DBConnection.

        Args:
            db_path: Path to the SQLite database.
        """
        self.db_path = db_path
        self.connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Establishes an asynchronous SQLite connection and configures it.

        Enables WAL (Write-Ahead Logging) journal mode and enforces Foreign Key constraints.
        Also configures the row factory to return Row objects.
        """
        self.connection = await aiosqlite.connect(self.db_path)
        self.connection.row_factory = aiosqlite.Row
        # WAL mode allows concurrent reads during a write transaction
        await self.connection.execute("PRAGMA journal_mode=WAL")
        await self.connection.execute("PRAGMA foreign_keys = ON")

    async def close(self) -> None:
        """Asynchronously closes the active SQLite connection if it exists."""
        if self.connection:
            await self.connection.close()
            self.connection = None
