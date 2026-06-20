import asyncio
from pathlib import Path

from database.connection import DBConnection
from database.migrations import run_migrations


async def initialize_database(db: DBConnection) -> None:
    schema_path = Path(__file__).parent / "schema.sql"

    schema = await asyncio.to_thread(schema_path.read_text, encoding="utf-8")

    assert db.connection is not None

    await db.connection.executescript(schema)
    await db.connection.commit()
    await run_migrations(db)
