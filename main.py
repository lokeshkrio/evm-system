# main.py

import asyncio
import logging
from contextlib import suppress

from database.connection import DBConnection
from database.init_db import initialize_database
from database.seed import DataSeeder

from repositories.vote_repository import VoteRepository
from repositories.candidate_repository import CandidateRepository
from repositories.metadata_repository import MetadataRepository
from repositories.event_repository import EventRepository

from services.audit_service import AuditService
from services.state_machine import ElectionStateMachine
from services.election_service import ElectionService

from server.rpc_dispatcher import RPCDispatcher
from server.connection_manager import ConnectionManager
from server.websocket_server import WebSocketServer
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


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


async def main() -> None:

    db = DBConnection("data/evm.db")
    websocket_server: WebSocketServer | None = None

    shutdown_event = asyncio.Event()

    try:

        # --------------------------
        # Database
        # --------------------------

        logger.info("Connecting database...")

        await db.connect()

        logger.info("Initializing database...")

        await initialize_database(db)

        logger.info("Seeding database...")

        await DataSeeder.seed(db)

        # --------------------------
        # Repositories
        # --------------------------

        vote_repository = VoteRepository(db)
        candidate_repository = CandidateRepository(db)
        metadata_repository = MetadataRepository(db)
        event_repository = EventRepository(db)

        # --------------------------
        # Services
        # --------------------------

        audit_service = AuditService()

        state_machine = ElectionStateMachine()

        election_service = ElectionService(
            audit_service=audit_service,
            state_machine=state_machine,
            candidate_repository=candidate_repository,
            metadata_repository=metadata_repository,
            vote_repository=vote_repository,
            event_repository=event_repository,
        )

        await election_service.initialize()

        # --------------------------
        # RPC Dispatcher
        # --------------------------

        dispatcher = RPCDispatcher()

        dispatcher.register(
            "cast_vote",
            election_service.cast_vote,
            CastVoteParams,
        )

        dispatcher.register(
            "start_election",
            election_service.start_election,
            StartElectionParams,
        )

        dispatcher.register(
            "enable_vote",
            election_service.enable_vote,
            EnableVoteParams,
        )

        dispatcher.register(
            "stop_election",
            election_service.stop_election,
            StopElectionParams,
        )

        dispatcher.register(
            "halt_election",
            election_service.halt_election,
            HaltElectionParams,
        )

        dispatcher.register(
            "resume_election",
            election_service.resume_election,
            ResumeElectionParams,
        )

        dispatcher.register(
            "get_status",
            election_service.get_status,
            GetStatusParams,
        )

        dispatcher.register(
            "get_state",
            election_service.get_state,
            GetStateParams,
        )

        dispatcher.register(
            "get_results",
            election_service.get_results,
            GetResultsParams,
        )

        # --------------------------
        # Connection Manager
        # --------------------------

        connection_manager = ConnectionManager()

        # --------------------------
        # WebSocket Server
        # --------------------------

        websocket_server = WebSocketServer(
            dispatcher=dispatcher,
            connection_manager=connection_manager,
            host="localhost",
            port=8765,
        )

        logger.info("Starting WebSocket server...")

        await websocket_server.start()

        logger.info("Server listening on ws://localhost:8765")

        # Run forever
        await shutdown_event.wait()

    except asyncio.CancelledError:

        logger.info("Main task cancelled.")

    except Exception:

        logger.exception("Fatal error during server execution.")

    finally:

        logger.info("Beginning shutdown...")

        if websocket_server is not None:

            with suppress(Exception):

                await websocket_server.stop()

        with suppress(Exception):

            await db.close()

        logger.info("Shutdown complete.")


if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        logger.info("Server stopped by user.")
