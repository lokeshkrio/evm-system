# server/websocket_server.py

import asyncio
import json
import logging

from pydantic import ValidationError
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from server.protocol import (
    RPCRequest,
    RPCError,
    RPCErrorResponse,
    ErrorCode,
)
from server.connection_manager import ConnectionManager
from server.rpc_dispatcher import RPCDispatcher

logger = logging.getLogger(__name__)


class WebSocketServer:

    def __init__(
        self,
        dispatcher: RPCDispatcher,
        connection_manager: ConnectionManager,
        host: str = "localhost",
        port: int = 8765,
    ) -> None:

        self.dispatcher = dispatcher
        self.connection_manager = connection_manager

        self.host = host
        self.port = port

    async def handler(
        self,
        websocket: ServerConnection,
    ) -> None:

        client_id = f"{websocket.remote_address[0]}" f":{websocket.remote_address[1]}"

        await self.connection_manager.connect(
            client_id,
            websocket,
        )

        logger.info(
            "Client connected: %s",
            client_id,
        )

        try:

            async for raw_message in websocket:

                if isinstance(
                    raw_message,
                    bytes,
                ):
                    raw_message = raw_message.decode("utf-8")

                response = await self._process_message(raw_message)

                if response is not None:

                    await websocket.send(response)

        except ConnectionClosed:

            logger.info(
                "Client disconnected: %s",
                client_id,
            )

        except Exception:

            logger.exception("Unexpected error in handler")

        finally:

            await self.connection_manager.disconnect(client_id)

    async def _process_message(
        self,
        raw_message: str,
    ) -> str | None:

        request_id = None

        # Parse JSON
        try:

            data = json.loads(raw_message)

        except json.JSONDecodeError:

            return RPCErrorResponse(
                error=RPCError(
                    code=ErrorCode.PARSE_ERROR,
                    message="Parse error",
                ),
                id=None,
            ).model_dump_json()

        try:

            if isinstance(
                data,
                dict,
            ):
                request_id = data.get("id")

            request = RPCRequest.model_validate(data)

            response = await self.dispatcher.dispatch(request)

            if response is None:
                return None

            return response.model_dump_json()

        except ValidationError:

            logger.warning("Invalid RPC request")

            return RPCErrorResponse(
                error=RPCError(
                    code=ErrorCode.INVALID_REQUEST,
                    message="Invalid request",
                ),
                id=request_id,
            ).model_dump_json()

        except Exception:

            logger.exception("Internal server error")

            return RPCErrorResponse(
                error=RPCError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="Internal error",
                ),
                id=request_id,
            ).model_dump_json()

    async def start(
        self,
    ) -> None:

        logger.info(
            "WebSocket server listening on ws://%s:%d",
            self.host,
            self.port,
        )

        async with serve(
            self.handler,
            self.host,
            self.port,
        ):

            await asyncio.Future()
