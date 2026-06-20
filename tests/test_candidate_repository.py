import pytest
import pytest_asyncio
from database.connection import DBConnection
from database.init_db import initialize_database
from models.candidate import Candidate
from repositories.candidate_repository import CandidateRepository

@pytest_asyncio.fixture
async def db_conn():
    # Use an in-memory SQLite database for testing
    db = DBConnection(":memory:")
    await db.connect()
    await initialize_database(db)
    yield db
    await db.close()

@pytest.mark.asyncio
async def test_candidate_repository_flow(db_conn):
    repo = CandidateRepository(db_conn)
    
    # Check that candidate does not exist initially
    assert not await repo.is_exists(1)
    
    # Add candidate
    candidate = Candidate(candidate_id=1, name="Alice", party="Dream Party", active=True)
    added = await repo.add(candidate)
    assert added is True
    
    # Check that candidate now exists
    assert await repo.is_exists(1)
    
    # Get candidate
    retrieved = await repo.get_candidate(1)
    assert retrieved is not None
    assert retrieved.candidate_id == 1
    assert retrieved.name == "Alice"
    assert retrieved.party == "Dream Party"
    assert retrieved.active is True
    
    # Add another candidate
    candidate2 = Candidate(candidate_id=2, name="Bob", party="Future Party", active=False)
    await repo.add(candidate2)
    
    # Get all candidates
    all_candidates = await repo.get_all_candidates()
    assert len(all_candidates) == 2
    assert all_candidates[0].name == "Alice"
    assert all_candidates[1].name == "Bob"
    assert all_candidates[1].active is False
    
    # Get all (compatibility method)
    all_legacy = await repo.get_all()
    assert len(all_legacy) == 2
    assert all_legacy[0].name == "Alice"
