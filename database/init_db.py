from pathlib import Path

from database.connection import DBConnection


async def initialize_database(db: DBConnection) -> None:
    """Initializes the SQLite database by running the schema SQL script.

    Args:
        db: The DBConnection instance holding the active database connection.
    """
    schema_path = Path(__file__).parent.joinpath("schema.sql")

    with open(schema_path, encoding="utf-8") as file:
        schema = file.read()

    assert db.connection is not None

    await db.connection.executescript(schema)
    await db.connection.commit()
