# server/rpc_dispatcher.py

from typing import Any, Awaitable, Callable

import logging
import time

from pydantic import BaseModel, ValidationError

import server.protocol as protocol
from models.enums import Role
from security.auth import authorize


RPCMethod = Callable[..., Awaitable[Any]]
logger = logging.getLogger(__name__)


class RPCDispatcher:
    """
    Registers and dispatches JSON-RPC methods.
    """

    def __init__(self, metrics_service: Any = None) -> None:
        self._methods: dict[str, RPCMethod] = {}
        self._params_models: dict[str, type[BaseModel]] = {}
        self._method_roles: dict[str, Role | None] = {}
        self.metrics_service = metrics_service

    @property
    def methods(self) -> tuple[str, ...]:
        return tuple(self._methods.keys())

    def register(
        self,
        name: str,
        func: RPCMethod,
        params_model: type[BaseModel] | None = None,
        required_role: Role | None = None,
    ) -> None:

        if name in self._methods:
            raise ValueError(f"RPC method '{name}' already registered")

        self._methods[name] = func
        if params_model is not None:
            self._params_models[name] = params_model
        self._method_roles[name] = required_role

    async def dispatch(
        self,
        request: protocol.RPCRequest,
    ) -> protocol.RPCResponse | protocol.RPCErrorResponse | None:
        start_time = time.time()
        success = False
        try:
            response = await self._dispatch_internal(request)
            success = not isinstance(response, protocol.RPCErrorResponse)
            return response
        finally:
            if self.metrics_service:
                latency = (time.time() - start_time) * 1000
                self.metrics_service.record_rpc_call(latency, success)

    async def _dispatch_internal(
        self,
        request: protocol.RPCRequest,
    ) -> protocol.RPCResponse | protocol.RPCErrorResponse | None:

        handler = self._methods.get(request.method)
        required_role = self._method_roles.get(request.method)

        if handler is None:

            if request.id is None:
                return None

            return protocol.error_response(
                request.id,
                protocol.ErrorCode.METHOD_NOT_FOUND,
                "Method not found",
            )

        if required_role is not None:
            if not authorize(request.api_key, required_role):
                if request.id is None:
                    return None
                return protocol.error_response(
                    request.id,
                    protocol.ErrorCode.INVALID_REQUEST,
                    "Unauthorized: Invalid or missing API key for required role",
                )

        try:

            params = request.params
            params_model = self._params_models.get(request.method)

            if params_model is not None:
                if params is None:
                    params = {}
                if not isinstance(params, dict):
                    if request.id is None:
                        return None
                    return protocol.error_response(
                        request.id,
                        protocol.ErrorCode.INVALID_PARAMS,
                        "Invalid params",
                    )
                validated_params = params_model.model_validate(params)
                result = await handler(**validated_params.model_dump())

            elif params is None:

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

            if request.id is None:
                return None

            return protocol.error_response(
                request.id,
                protocol.ErrorCode.INVALID_PARAMS,
                "Validation failed",
            )

        except TypeError:

            if request.id is None:
                return None

            return protocol.error_response(
                request.id,
                protocol.ErrorCode.INVALID_PARAMS,
                "Invalid params",
            )

        except Exception:

            logger.exception("Unhandled error while dispatching RPC method %s", request.method)

            if request.id is None:
                return None

            return protocol.error_response(
                request.id,
                protocol.ErrorCode.INTERNAL_ERROR,
                "Internal error",
            )
