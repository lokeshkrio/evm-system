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


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


async def main() -> None:

    db = DBConnection("data/evm.db")
    websocket_server = None

    try:
        # -----------------------------------
        # Database
        # -----------------------------------

        logging.info("Connecting database...")

        await db.connect()

        await initialize_database(db)
        await DataSeeder.seed(db)

        # -----------------------------------
        # Repositories
        # -----------------------------------

        vote_repository = VoteRepository(db)
        candidate_repository = CandidateRepository(db)
        metadata_repository = MetadataRepository(db)
        event_repository = EventRepository(db)

        # -----------------------------------
        # Services
        # -----------------------------------

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

        # -----------------------------------
        # RPC Dispatcher
        # -----------------------------------

        dispatcher = RPCDispatcher()

        dispatcher.register("cast_vote", election_service.cast_vote)
        dispatcher.register("start_election", election_service.start_election)
        dispatcher.register("stop_election", election_service.stop_election)
        dispatcher.register("halt_election", election_service.halt_election)
        dispatcher.register("get_status", election_service.get_status)
        dispatcher.register("get_state", election_service.get_state)
        dispatcher.register("get_results", election_service.get_results)

        # -----------------------------------
        # Connection Manager
        # -----------------------------------

        connection_manager = ConnectionManager()

        # -----------------------------------
        # WebSocket Server
        # -----------------------------------

        websocket_server = WebSocketServer(
            dispatcher=dispatcher,
            connection_manager=connection_manager,
            host="localhost",
            port=8765,
        )

        logging.info("Starting WebSocket server...")

        await websocket_server.start()

        logging.info("Server running on ws://localhost:8765")

        # Keep process alive forever
        await asyncio.Future()

    except asyncio.CancelledError:
        logging.info("Main task cancelled.")

    finally:

        logging.info("Beginning shutdown...")

        # -----------------------------
        # Stop websocket server
        # -----------------------------
        if websocket_server is not None:
            with suppress(Exception):
                await websocket_server.stop()

        # -----------------------------
        # Close database
        # -----------------------------
        with suppress(Exception):
            await db.close()

        logging.info("Shutdown complete.")


if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logging.info("Server stopped by user.")
