import pytest
import pytest_asyncio
from database.connection import DBConnection
from database.init_db import initialize_database
from database.unit_of_work import UnitOfWork
from models.enums import ElectionState
from services.state_machine import PersistentElectionStateMachine

@pytest_asyncio.fixture
async def db_conn():
    db = DBConnection(":memory:")
    await db.connect()
    await initialize_database(db)
    yield db
    await db.close()

@pytest.mark.asyncio
async def test_persistent_state_machine(db_conn):
    sm = PersistentElectionStateMachine()
    
    async with UnitOfWork(db_conn) as uow:
        state = await sm.get_state(uow)
        assert state == ElectionState.INITIALIZED
        
        # Start
        next_state = await sm.start_election(uow)
        assert next_state == ElectionState.STARTED
        
        # Enable vote
        next_state = await sm.enable_vote(uow)
        assert next_state == ElectionState.VOTING
        
        # Vote casted
        next_state = await sm.vote_casted(uow)
        assert next_state == ElectionState.STARTED
        
        # Enable vote again
        next_state = await sm.enable_vote(uow)
        
        # Halt
        next_state = await sm.halt(uow)
        assert next_state == ElectionState.HALTED
        
        # Resume
        next_state = await sm.resume(uow)
        assert next_state == ElectionState.STARTED
        
        # End
        next_state = await sm.end(uow)
        assert next_state == ElectionState.ENDED
