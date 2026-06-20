from repositories.base_repository import BaseRepository


class EventRepository(BaseRepository):
    """SQL access for the append-only, hash-chained event table."""

    async def get_last_hash(self) -> str | None:
        cursor = await self.conn.execute(
            """
            SELECT event_hash
            FROM events
            ORDER BY event_id DESC
            LIMIT 1
            """
        )
        row = await cursor.fetchone()
        return row["event_hash"] if row else None

    async def append_event(
        self,
        event_type: str,
        payload: str,
        timestamp: str,
        previous_hash: str,
        event_hash: str,
    ) -> None:
        await self.conn.execute(
            """
            INSERT INTO events(
                event_type,
                payload,
                timestamp,
                previous_hash,
                event_hash
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_type, payload, timestamp, previous_hash, event_hash),
        )

    async def list_events(self) -> list[dict[str, str | int]]:
        cursor = await self.conn.execute(
            """
            SELECT
                event_id,
                event_type,
                payload,
                timestamp,
                previous_hash,
                event_hash
            FROM events
            ORDER BY event_id
            """
        )
        return [dict(row) for row in await cursor.fetchall()]
