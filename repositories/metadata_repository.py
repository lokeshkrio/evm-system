from repositories.base_repository import BaseRepository


class MetadataRepository(BaseRepository):
    """Repository handling database operations for key-value pair metadata storage."""

    async def get(self, key: str) -> str | None:
        """Retrieves a metadata value associated with a specific key.

        Args:
            key: The unique string key for the metadata.

        Returns:
            The string value if found, or None.
        """
        cursor = await self.conn.execute(
            """
            SELECT value
            FROM metadata
            WHERE key = ?
            """,
            (key,),
        )
        row = await cursor.fetchone()
        return row["value"] if row else None

    async def set(self, key: str, value: str) -> None:
        """Sets or replaces a metadata key-value pair in the database.

        Args:
            key: The unique string key.
            value: The string value to store.
        """
        await self.conn.execute(
            """
            INSERT OR REPLACE
            INTO metadata(key, value)
            VALUES (?, ?)
            """,
            (key, value),
        )
        await self.conn.commit()
