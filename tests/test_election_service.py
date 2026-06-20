import pytest
import pytest_asyncio
from database.connection import DBConnection
from database.init_db import initialize_database
from database.unit_of_work import UnitOfWork
from events.event_bus import EventBus
from models.enums import ElectionState
from services.election_service import ElectionService
from services.state_machine import PersistentElectionStateMachine

@pytest_asyncio.fixture
async def db_conn():
    db = DBConnection(":memory:")
    await db.connect()
    await initialize_database(db)
    yield db
    await db.close()

@pytest.mark.asyncio
async def test_election_service_flow(db_conn):
    event_bus = EventBus()
    service = ElectionService(
        unit_of_work_factory=lambda: UnitOfWork(db_conn),
        state_machine=PersistentElectionStateMachine(),
        event_bus=event_bus,
    )
    
    await service.initialize()
    status = await service.get_status()
    assert status["state"] == ElectionState.INITIALIZED.value
    
    res = await service.start_election()
    assert res["success"] is True
    
    status = await service.get_status()
    assert status["state"] == ElectionState.STARTED.value
    
    res = await service.enable_vote()
    assert res["success"] is True
