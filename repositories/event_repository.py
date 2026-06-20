from repositories.base_repository import BaseRepository


class EventRepository(BaseRepository):
    """Repository handling database operations for the events table."""

    async def append_event(self, event_type: str, payload: str, timestamp: str) -> None:
        """Appends a new event entry into the event log/history database.

        Args:
            event_type: The string event type identifier (e.g. 'vote_cast').
            payload: JSON string payload representing event metadata.
            timestamp: ISO 8601 formatted timestamp of the event.
        """
        await self.conn.execute(
            """
            INSERT INTO events(
                event_type,
                payload,
                timestamp
            )
            VALUES (?, ?, ?)
            """,
            (event_type, payload, timestamp),
        )
        await self.conn.commit()
