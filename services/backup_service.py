import json
import logging
from pathlib import Path

from database.connection import DBConnection

logger = logging.getLogger(__name__)


class BackupService:
    """Service to export and restore complete database state snapshots."""

    def __init__(self, db: DBConnection) -> None:
        self.db = db
        # Order matters for foreign key constraints: Insert in this order, delete in reverse.
        self._tables = ["candidates", "voters", "votes", "metadata", "events", "terminals"]

    async def export_snapshot(self, filepath: str = "snapshot.json") -> None:
        """Exports the entire database state to a JSON snapshot."""
        logger.info(f"Exporting snapshot to {filepath}")
        
        async with self.db.transaction():
            data = {}
            for table in self._tables:
                cursor = await self.db.execute(f"SELECT * FROM {table}")
                rows = await cursor.fetchall()
                data[table] = [dict(row) for row in rows]

        Path(filepath).write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info("Snapshot export complete.")

    async def restore_snapshot(self, filepath: str = "snapshot.json") -> None:
        """Restores the database state from a JSON snapshot, overwriting current state."""
        logger.warning(f"Restoring snapshot from {filepath}. This replaces all current data.")
        
        content = Path(filepath).read_text(encoding="utf-8")
        data = json.loads(content)

        async with self.db.transaction():
            for table in reversed(self._tables):
                await self.db.execute(f"DELETE FROM {table}")

            for table in self._tables:
                rows = data.get(table, [])
                if not rows:
                    continue
                keys = list(rows[0].keys())
                placeholders = ",".join(["?"] * len(keys))
                columns = ",".join(keys)
                query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

                for row in rows:
                    values = tuple(row[k] for k in keys)
                    await self.db.execute(query, values)
                    
        logger.info("Snapshot restoration complete.")
