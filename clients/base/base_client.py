import asyncio
import logging
import websockets
import uuid
import json

logger = logging.getLogger(__name__)


class BaseClient:
    def __init__(self, uri: str, api_key: str | None = None):
        self.uri = uri
        self.api_key = api_key
        self.websocket = None
        self._request_id = str(uuid.uuid4())
        self._pending_requests: dict[str, asyncio.Future] = {}
        self._listen_task: asyncio.Task | None = None

    async def connect(self):
        """Establishes connection and starts the background listener."""
        self.websocket = await websockets.connect(self.uri)
        # Start a background task to listen for incoming messages/notifications
        self._listen_task = asyncio.create_task(self._listen_loop())

    async def close(self) -> None:
        """Cancels background tasks and closes the connection cleanly."""
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        if self.websocket:
            await self.websocket.close()

    async def send_request(
        self, method: str, params: dict | list | None = None
    ) -> dict | None:
        """Sends a JSON RPC request and waits for a response.

        Returns the 'result' field of the response, or raises an Exception on JSON-RPC error.
        """
        if not self.websocket:
            raise ConnectionError("[ERROR]: WebSocket is not connected.")

        # Construct a string request ID containing UUIDv4 and a deterministic salt from netloc
        netloc = self.uri.replace("ws://", "").replace("wss://", "").split("/")[0]
        salt = netloc.replace(":", "_").replace(".", "_")
        request_id = f"{uuid.uuid4()}_{salt}"

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params if params is not None else {},
            "id": request_id,
            "api_key": self.api_key,
        }

        # Create a Future object to hold the response when it arrives
        future = asyncio.get_running_loop().create_future()
        self._pending_requests[request_id] = future

        try:
            await self.websocket.send(json.dumps(payload))
            # Wait for the response (or timeout)
            response = await asyncio.wait_for(future, timeout=10)
            if response is None:
                return None
            if "error" in response:
                error_info = response["error"]
                message = error_info.get("message", "Unknown error")
                raise Exception(message)
            return response.get("result")
        except asyncio.TimeoutError:
            logger.warning(
                "[WARNING]: Timeout waiting for response for request_id %s", request_id
            )
            return None
        except Exception as e:
            logger.error(
                "[ERROR]: Error waiting for response for request_id %s: %s",
                request_id,
                e,
            )
            raise
        finally:
            self._pending_requests.pop(request_id, None)

    async def request(self, method: str, params: list) -> str:
        """Sends a JSON RPC request and waits for a response (legacy compatibility wrapper)."""
        if not self.websocket:
            raise ConnectionError("[ERROR]: WebSocket is not connected.")

        netloc = self.uri.replace("ws://", "").replace("wss://", "").split("/")[0]
        salt = netloc.replace(":", "_").replace(".", "_")
        request_id = f"{uuid.uuid4()}_{salt}"

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id,
            "api_key": self.api_key,
        }

        future = asyncio.get_running_loop().create_future()
        self._pending_requests[request_id] = future

        try:
            await self.websocket.send(json.dumps(payload))
            response = await asyncio.wait_for(future, timeout=10)
            return json.dumps(response) if response is not None else None
        except asyncio.TimeoutError:
            logger.warning(
                "[WARNING]: Timeout waiting for response for request_id %s", request_id
            )
            return None
        except Exception as e:
            logger.error(
                "[ERROR]: Error waiting for response for request_id %s: %s",
                request_id,
                e,
            )
            return None
        finally:
            self._pending_requests.pop(request_id, None)

    async def _listen_loop(self):
        """Listens for incoming messages/notifications."""
        try:
            async for raw_message in self.websocket:
                try:
                    data = json.loads(raw_message)

                    # Handle Standard Responses
                    if isinstance(data, dict) and "id" in data:
                        req_id = data["id"]
                        if req_id in self._pending_requests:
                            self._pending_requests[req_id].set_result(data)

                    # Handle Broadcast Notifications (No ID)
                    elif isinstance(data, dict) and "method" in data:
                        await self.handle_notification(data)

                except json.JSONDecodeError as e:
                    logger.error(
                        "[ERROR]: Failed to decode JSON message for request_id %s: %s",
                        self._request_id,
                        e,
                    )
                    continue

                except Exception as e:
                    logger.error(
                        "[ERROR]: Failed to handle message for request_id %s: %s",
                        self._request_id,
                        e,
                    )
                    continue

        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed by the remote cluster server.")
        except asyncio.CancelledError:
            logger.info("Listen loop cancelled.")
        except Exception as e:
            logger.error("[ERROR]: Listen loop failed: %s", e)

    async def _handle_message(self, message: str) -> None:
        """Handles incoming messages/notifications."""
        try:
            data = json.loads(message)
            if "id" in data:
                request_id = data["id"]
                if request_id in self._pending_requests:
                    future = self._pending_requests[request_id]
                    if "result" in data:
                        future.set_result(data["result"])
                    elif "error" in data:
                        future.set_exception(Exception(data["error"]))
                    del self._pending_requests[request_id]
            else:
                self._handle_notification(data)
        except json.JSONDecodeError:
            logger.error(
                "[ERROR]: Failed to decode JSON message for request_id %s: %s",
                self._request_id,
                message,
            )

    async def handle_notification(self, notification: dict) -> None:
        """Hook method for subclasses to override to process broadcast alerts."""
        # e.g., print live updates like {"method": "election_started"}
        pass
