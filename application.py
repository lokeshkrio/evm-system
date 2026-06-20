import asyncio
import logging
from types import SimpleNamespace

from config import settings
from database.connection import DBConnection
from database.init_db import initialize_database
from database.seed import DataSeeder
from database.unit_of_work import UnitOfWork
from events.event_bus import EventBus
from events.subscribers import AuditSubscriber, BackupSubscriber, MetricsSubscriber, WebSocketSubscriber
from server.connection_manager import ConnectionManager
from server.protocol import (
    CastVoteParams,
    EnableVoteParams,
    GetResultsParams,
    GetMetricsParams,
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
from services.backup_service import BackupService
from services.election_service import ElectionService
from services.metrics_service import MetricsService
from services.state_machine import PersistentElectionStateMachine
from models.enums import Role

logger = logging.getLogger(__name__)


class Application:
    """Composition root and lifecycle owner for the EVM backend."""

    def __init__(self) -> None:
        self.db = DBConnection(settings.db_path)
        self.host = settings.host
        self.port = settings.port
        self.connection_manager = ConnectionManager()
        
        self.repositories = SimpleNamespace()
        self.services = SimpleNamespace()
        
        self.services.metrics = MetricsService(self.connection_manager)
        self.services.backup = BackupService(self.db)
        self.metrics = MetricsSubscriber(self.services.metrics)
        self.dispatcher: RPCDispatcher | None = None
        self.server: WebSocketServer | None = None
        
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        logger.info("Connecting and initializing database")
        await self.db.connect()
        await initialize_database(self.db)
        await DataSeeder.seed(self.db)

        event_bus = EventBus()
        self.services.audit = AuditService()
        event_bus.subscribe("*", AuditSubscriber(self.services.audit))
        event_bus.subscribe("*", self.metrics)
        event_bus.subscribe("*", WebSocketSubscriber(self.connection_manager))
        event_bus.subscribe("*", BackupSubscriber(self.services.backup))

        self.services.election = ElectionService(
            unit_of_work_factory=lambda: UnitOfWork(self.db),
            state_machine=PersistentElectionStateMachine(),
            event_bus=event_bus,
        )
        await self.services.election.initialize()

        self.dispatcher = self._build_dispatcher(self.services.election, self.services.metrics, self.db)
        self.server = WebSocketServer(
            dispatcher=self.dispatcher,
            connection_manager=self.connection_manager,
            host=self.host,
            port=self.port,
        )
        await self.server.start()
        logger.info("Server listening on ws://%s:%d", self.host, self.port)

    async def run(self) -> None:
        await self._shutdown_event.wait()

    async def stop(self) -> None:
        self._shutdown_event.set()
        try:
            if self.server is not None:
                await self.server.stop()
                self.server = None
        finally:
            await self.db.close()

    @staticmethod
    def _build_dispatcher(service: ElectionService, metrics: MetricsService, db: DBConnection) -> RPCDispatcher:
        dispatcher = RPCDispatcher(metrics_service=metrics, db=db)
        dispatcher.register("cast_vote", service.cast_vote, CastVoteParams, Role.TERMINAL)
        dispatcher.register("start_election", service.start_election, StartElectionParams, Role.ADMIN)
        dispatcher.register("enable_vote", service.enable_vote, EnableVoteParams, Role.ADMIN)
        dispatcher.register("stop_election", service.stop_election, StopElectionParams, Role.ADMIN)
        dispatcher.register("halt_election", service.halt_election, HaltElectionParams, Role.ADMIN)
        dispatcher.register("resume_election", service.resume_election, ResumeElectionParams, Role.ADMIN)
        dispatcher.register("get_status", service.get_status, GetStatusParams)
        dispatcher.register("get_state", service.get_state, GetStateParams)
        dispatcher.register("get_results", service.get_results, GetResultsParams)
        dispatcher.register("get_metrics", metrics.get_metrics, GetMetricsParams)
        return dispatcher
