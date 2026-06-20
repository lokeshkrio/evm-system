from pathlib import Path

from database.connection import DBConnection


async def initialize_database(db: DBConnection) -> None:
    schema_path = Path(__file__).parent / "schema.sql"

    with open(schema_path, encoding="utf-8") as file:
        schema = file.read()

    assert db.connection is not None

    await db.connection.executescript(schema)
    await db.connection.commit()
