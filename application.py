import logging

from database.connection import DBConnection
from database.init_db import initialize_database
from database.seed import DataSeeder
from database.unit_of_work import UnitOfWork
from events.event_bus import EventBus
from events.subscribers import AuditSubscriber, MetricsSubscriber, WebSocketSubscriber
from server.connection_manager import ConnectionManager
from server.protocol import (
    CastVoteParams,
    EnableVoteParams,
    GetResultsParams,
    GetStateParams,
    GetStatusParams,
    HaltElectionParams,
    ResumeElectionParams,
    StartElectionParams,
    StopElectionParams,
)
from server.rpc_dispatcher import RPCDispatcher
from server.websocket_server import WebSocketServer
from services.audit_service import AuditService
from services.election_service import ElectionService
from services.state_machine import ElectionStateMachine

logger = logging.getLogger(__name__)


class Application:
    """Composition root and lifecycle owner for the EVM backend."""

    def __init__(
        self,
        db_path: str = "data/evm.db",
        host: str = "localhost",
        port: int = 8765,
    ) -> None:
        self.db = DBConnection(db_path)
        self.host = host
        self.port = port
        self.connection_manager = ConnectionManager()
        self.metrics = MetricsSubscriber()
        self.election_service: ElectionService | None = None
        self.websocket_server: WebSocketServer | None = None

    async def start(self) -> None:
        logger.info("Connecting and initializing database")
        await self.db.connect()
        await initialize_database(self.db)
        await DataSeeder.seed(self.db)

        event_bus = EventBus()
        event_bus.subscribe("*", AuditSubscriber(AuditService()))
        event_bus.subscribe("*", self.metrics)
        event_bus.subscribe("*", WebSocketSubscriber(self.connection_manager))

        self.election_service = ElectionService(
            unit_of_work_factory=lambda: UnitOfWork(self.db),
            state_machine=ElectionStateMachine(),
            event_bus=event_bus,
        )
        await self.election_service.initialize()

        dispatcher = self._build_dispatcher(self.election_service)
        self.websocket_server = WebSocketServer(
            dispatcher=dispatcher,
            connection_manager=self.connection_manager,
            host=self.host,
            port=self.port,
        )
        await self.websocket_server.start()

    async def stop(self) -> None:
        try:
            if self.websocket_server is not None:
                await self.websocket_server.stop()
                self.websocket_server = None
        finally:
            await self.db.close()

    @staticmethod
    def _build_dispatcher(service: ElectionService) -> RPCDispatcher:
        dispatcher = RPCDispatcher()
        dispatcher.register("cast_vote", service.cast_vote, CastVoteParams)
        dispatcher.register("start_election", service.start_election, StartElectionParams)
        dispatcher.register("enable_vote", service.enable_vote, EnableVoteParams)
        dispatcher.register("stop_election", service.stop_election, StopElectionParams)
        dispatcher.register("halt_election", service.halt_election, HaltElectionParams)
        dispatcher.register("resume_election", service.resume_election, ResumeElectionParams)
        dispatcher.register("get_status", service.get_status, GetStatusParams)
        dispatcher.register("get_state", service.get_state, GetStateParams)
        dispatcher.register("get_results", service.get_results, GetResultsParams)
        return dispatcher
