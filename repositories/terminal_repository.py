from typing import Any
from database.connection import DBConnection


class TerminalRepository:
    def __init__(self, db: DBConnection) -> None:
        self.db = db

    async def get_by_secret(self, secret_key: str) -> dict[str, Any] | None:
        cursor = await self.db.execute(
            "SELECT * FROM terminals WHERE secret_key = ?", (secret_key,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
