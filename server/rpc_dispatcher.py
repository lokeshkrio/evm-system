# server/rpc_dispatcher.py

from typing import Any, Awaitable, Callable

from pydantic import ValidationError

import server.protocol as protocol


RPCMethod = Callable[..., Awaitable[Any]]


class RPCDispatcher:
    """
    Registers and dispatches JSON-RPC methods.
    """

    def __init__(self) -> None:
        self._methods: dict[str, RPCMethod] = {}

    @property
    def methods(self) -> tuple[str, ...]:
        return tuple(self._methods.keys())

    def register(
        self,
        name: str,
        func: RPCMethod,
    ) -> None:

        if name in self._methods:
            raise ValueError(f"RPC method '{name}' already registered")

        self._methods[name] = func

    async def dispatch(
        self,
        request: protocol.RPCRequest,
    ) -> protocol.RPCResponse | protocol.RPCErrorResponse | None:

        handler = self._methods.get(request.method)

        if handler is None:

            return protocol.error_response(
                request.id,
                protocol.ErrorCode.METHOD_NOT_FOUND,
                "Method not found",
            )

        try:

            params = request.params

            if params is None:

                result = await handler()

            elif isinstance(params, dict):

                result = await handler(**params)

            elif isinstance(params, list):

                result = await handler(*params)

            else:

                return protocol.error_response(
                    request.id,
                    protocol.ErrorCode.INVALID_PARAMS,
                    "Invalid params",
                )

            # Notification
            if request.id is None:
                return None

            return protocol.RPCResponse(
                id=request.id,
                result=result,
            )

        except ValidationError:

            return protocol.error_response(
                request.id,
                protocol.ErrorCode.INVALID_PARAMS,
                "Validation failed",
            )

        except TypeError:

            return protocol.error_response(
                request.id,
                protocol.ErrorCode.INVALID_PARAMS,
                "Invalid params",
            )

        except Exception as e:

            return protocol.error_response(
                request.id,
                protocol.ErrorCode.INTERNAL_ERROR,
                str(e),
            )
