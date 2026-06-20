import pytest
import pytest_asyncio
import os
from database.connection import DBConnection
from database.init_db import initialize_database
from services.backup_service import BackupService

@pytest_asyncio.fixture
async def db_conn():
    db = DBConnection(":memory:")
    await db.connect()
    await initialize_database(db)
    yield db
    await db.close()

@pytest.mark.asyncio
async def test_snapshot_restore(db_conn):
    backup = BackupService(db_conn)
    snapshot_path = "tests/test_snapshot.json"
    
    # Insert initial data
    await db_conn.execute("INSERT INTO candidates (candidate_id, name, party) VALUES (1, 'Alice', 'Party A')")
    
    # Export snapshot
    await backup.export_snapshot(snapshot_path)
    assert os.path.exists(snapshot_path)
    
    # Clear the table to simulate data loss
    await db_conn.execute("DELETE FROM candidates")
    
    # Restore from snapshot
    await backup.restore_snapshot(snapshot_path)
    
    # Verify data
    cursor = await db_conn.execute("SELECT * FROM candidates")
    rows = await cursor.fetchall()
    assert len(rows) == 1
    assert rows[0]["name"] == "Alice"
    
    # Cleanup
    if os.path.exists(snapshot_path):
        os.remove(snapshot_path)
