import logging

from database.connection import DBConnection
from utils.hashing import GENESIS_EVENT_HASH, hash_database_event

logger = logging.getLogger(__name__)

SCHEMA_VERSION_KEY = "schema_version"
CURRENT_SCHEMA_VERSION = 2


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
        version = 1

    if version < 2:
        await _add_event_hash_chain(db)
        await _set_schema_version(db, 2)
        logger.info("Database migrated to schema version 2")


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


async def _add_event_hash_chain(db: DBConnection) -> None:
    assert db.connection is not None

    columns_cursor = await db.connection.execute("PRAGMA table_info(events)")
    columns = {row["name"] for row in await columns_cursor.fetchall()}
    if {"previous_hash", "event_hash"}.issubset(columns):
        return

    cursor = await db.connection.execute(
        """
        SELECT sequence_no, event_type, payload, timestamp
        FROM events
        ORDER BY sequence_no
        """
    )
    existing_events = await cursor.fetchall()

    async with db.transaction():
        await db.connection.execute(
            """
            CREATE TABLE events_new (
                sequence_no INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                event_hash TEXT UNIQUE NOT NULL
            )
            """
        )

        previous_hash = GENESIS_EVENT_HASH
        for event in existing_events:
            event_hash = hash_database_event(
                previous_hash,
                event["event_type"],
                event["payload"],
                event["timestamp"],
            )
            await db.connection.execute(
                """
                INSERT INTO events_new(
                    sequence_no,
                    event_type,
                    payload,
                    timestamp,
                    previous_hash,
                    event_hash
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event["sequence_no"],
                    event["event_type"],
                    event["payload"],
                    event["timestamp"],
                    previous_hash,
                    event_hash,
                ),
            )
            previous_hash = event_hash

        await db.connection.execute("DROP TABLE events")
        await db.connection.execute("ALTER TABLE events_new RENAME TO events")
