from websockets.asyncio.server import ServerConnection
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # Map device/user IDs to their active websocket connection
        self._connections: dict[str, ServerConnection] = {}

    @property
    def count(self) -> int:

        return len(self._connections)

    async def connect(self, client_id: str, connection: ServerConnection) -> None:
        self._connections[client_id] = connection

    async def disconnect(self, client_id: str) -> None:
        self._connections.pop(client_id, None)
        logger.info(
            "Client %s disconnected",
            client_id,
        )

    async def send_to_client(self, client_id: str, message: str) -> None:
        """Finds the client by ID and sends them a direct message."""
        connection = self._connections.get(client_id)
        if connection:
            try:
                await connection.send(message)
            except Exception:
                await self.disconnect(client_id)
                logger.info(
                    "Client %s disconnected",
                    client_id,
                )

    async def broadcast(self, message: str) -> None:
        """Sends a message to absolutely everyone connected."""
        for client_id, connection in list(self._connections.items()):
            try:
                await connection.send(message)
            except Exception:
                await self.disconnect(client_id)
                logger.info(
                    "Client %s disconnected",
                    client_id,
                )
