from typing import Callable, Awaitable, Any
import server.protocol as protocol
from pydantic import ValidationError

RPCMethod = Callable[[protocol.RPCRequest], Awaitable[dict[str, Any]]]


class RPCDispatcher:
    """A dispatcher that registers and
    routes JSON-RPC methods to their handlers.

    It maps string method names to their corresponding asynchronous handlers,
    validates the incoming request parameters, unpacks them appropriately,
    and executes the handlers.
    """

    def __init__(self) -> None:
        """Initializes the RPCDispatcher with an empty registry of methods."""
        self._method: dict[str, RPCMethod] = {}

    def register(self, name: str, func: RPCMethod) -> None:
        """Registers a handler function under a specific method name.

        Args:
            name: The JSON-RPC method name (e.g., 'cast_vote').
            func: The asynchronous callable that handles this method.
        """
        self._method[name] = func

    async def dispatch(
        self, request: protocol.RPCRequest
    ) -> protocol.RPCErrorResponse | protocol.RPCResponse:
        """Dispatches an RPC request to its registered handler.

        This method validates if the requested handler exists, formats the
        parameters, executes the handler asynchronously, and returns either a
        success or error RPC response.

        Args:
            request: RPCRequest object containing the method, params, and ID.

        Returns:
            An RPCResponse on success or an RPCErrorResponse on failure.
        """
        handler = self._method.get(request.method)
        if handler is None:
            return protocol.error_response(
                request.id,
                protocol.ErrorCode.METHOD_NOT_FOUND,
                "Method not found",
            )

        try:
            params = (
                request.params
                if (isinstance(request.params, (dict, list)) or request.params is None)
                else ()
            )
            if isinstance(params, dict):
                result = await handler(**params)
            else:
                result = await handler(*params)

            # Notification
            if request.id is None:
                return None

            return protocol.RPCResponse(id=request.id, result=result)
        except TypeError:

            return protocol.RPCErrorResponse(
                id=request.id,
                error=protocol.RPCError(
                    code=protocol.ErrorCode.INVALID_PARAMS,
                    message="Invalid params",
                ),
            )

        except ValidationError:

            return protocol.RPCErrorResponse(
                id=request.id,
                error=protocol.RPCError(
                    code=protocol.ErrorCode.INVALID_PARAMS,
                    message="Validation failed",
                ),
            )
        except Exception as e:
            return protocol.error_response(
                request.id,
                protocol.ErrorCode.INTERNAL_ERROR,
                str(e),
            )
