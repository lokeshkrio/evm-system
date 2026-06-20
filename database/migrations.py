import logging

from database.connection import DBConnection

logger = logging.getLogger(__name__)

SCHEMA_VERSION_KEY = "schema_version"
CURRENT_SCHEMA_VERSION = 1


async def run_migrations(db: DBConnection) -> None:
    """Apply small, ordered SQLite migrations to an initialized database."""
    if db.connection is None:
        raise RuntimeError("Database connection not established")

    cursor = await db.connection.execute(
        "SELECT value FROM metadata WHERE key = ?",
        (SCHEMA_VERSION_KEY,),
    )
    row = await cursor.fetchone()
    version = int(row["value"]) if row else 0

    if version > CURRENT_SCHEMA_VERSION:
        raise RuntimeError(
            f"Database schema version {version} is newer than supported "
            f"version {CURRENT_SCHEMA_VERSION}"
        )

    if version < 1:
        await _add_vote_candidate_foreign_key(db)
        await _set_schema_version(db, 1)
        logger.info("Database migrated to schema version 1")


async def _add_vote_candidate_foreign_key(db: DBConnection) -> None:
    assert db.connection is not None

    cursor = await db.connection.execute("PRAGMA foreign_key_list(votes)")
    foreign_keys = await cursor.fetchall()
    if any(row["from"] == "candidate_id" for row in foreign_keys):
        return

    orphan_cursor = await db.connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM votes AS v
        LEFT JOIN candidates AS c ON c.candidate_id = v.candidate_id
        WHERE c.candidate_id IS NULL
        """
    )
    orphan_count = (await orphan_cursor.fetchone())["total"]
    if orphan_count:
        raise RuntimeError(
            f"Cannot migrate votes table: {orphan_count} vote(s) reference "
            "missing candidates"
        )

    await db.connection.execute("PRAGMA foreign_keys=OFF")
    try:
        await db.connection.executescript(
            """
            BEGIN IMMEDIATE;
            CREATE TABLE votes_new (
                vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
                voter_hash TEXT UNIQUE NOT NULL,
                candidate_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (candidate_id)
                    REFERENCES candidates(candidate_id) ON DELETE RESTRICT
            );
            INSERT INTO votes_new(vote_id, voter_hash, candidate_id, timestamp)
            SELECT vote_id, voter_hash, candidate_id, timestamp FROM votes;
            DROP TABLE votes;
            ALTER TABLE votes_new RENAME TO votes;
            COMMIT;
            """
        )
    except BaseException:
        await db.connection.rollback()
        raise
    finally:
        await db.connection.execute("PRAGMA foreign_keys=ON")
        await db.connection.commit()


async def _set_schema_version(db: DBConnection, version: int) -> None:
    assert db.connection is not None
    await db.connection.execute(
        """
        INSERT INTO metadata(key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (SCHEMA_VERSION_KEY, str(version)),
    )
    await db.connection.commit()
