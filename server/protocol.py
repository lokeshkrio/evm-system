from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Literal
from enum import Enum
import json


class Commands(str, Enum):
    """Supported JSON-RPC command methods in the EVM system."""
    CAST_VOTE = "cast_vote"
    START_ELECTION = "start_election"
    STOP_ELECTION = "stop_election"
    HALT_ELECTION = "halt_election"
    ENABLE_VOTE = "enable_vote"
    RESUME_ELECTION = "resume_election"
    GET_STATUS = "get_status"
    GET_STATE = "get_state"
    GET_RESULTS = "get_results"
    GET_AUDIT_LOGS = "get_audit_logs"


class ErrorCode(int, Enum):
    """JSON-RPC 2.0 standard error codes."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


class ParamsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CastVoteParams(ParamsModel):
    """Parameters required to cast a vote."""
    voter_hash: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-fA-F]{64}$")
    candidate_id: int = Field(gt=0)


class StartElectionParams(ParamsModel):
    """Parameters for starting an election (none required)."""
    pass


class StopElectionParams(ParamsModel):
    """Parameters for stopping an election (none required)."""
    pass


class HaltElectionParams(ParamsModel):
    """Parameters for halting an election (none required)."""
    pass


class EnableVoteParams(ParamsModel):
    """Parameters for enabling a single vote (none required)."""
    pass


class ResumeElectionParams(ParamsModel):
    """Parameters for resuming a halted election (none required)."""
    pass


class GetStatusParams(ParamsModel):
    """Parameters for retrieving election status (none required)."""
    pass


class GetStateParams(ParamsModel):
    """Parameters for retrieving election state (none required)."""
    pass


class GetResultsParams(ParamsModel):
    """Parameters for retrieving election results (none required)."""
    pass


class GetAuditLogsParams(ParamsModel):
    """Parameters for retrieving audit logs (none required)."""
    pass


class RPCRequest(BaseModel):
    """Base schema for general JSON-RPC requests."""
    model_config = ConfigDict(extra="forbid")

    jsonrpc: Literal["2.0"]
    method: str = Field(min_length=1)
    params: dict[str, Any] | list[Any] | None = None
    id: str | int | None = None


class CastVoteRequest(BaseModel):
    """Schema validation for a Cast Vote RPC request."""
    jsonrpc: str = "2.0"
    method: Literal[Commands.CAST_VOTE]
    params: CastVoteParams
    id: str | int


class StartElectionRequest(BaseModel):
    """Schema validation for a Start Election RPC request."""
    jsonrpc: str = "2.0"
    method: Literal[Commands.START_ELECTION]
    params: StartElectionParams
    id: str | int


class StopElectionRequest(BaseModel):
    """Schema validation for a Stop Election RPC request."""
    jsonrpc: str = "2.0"
    method: Literal[Commands.STOP_ELECTION]
    params: StopElectionParams
    id: str | int


class HaltElectionRequest(BaseModel):
    """Schema validation for a Halt Election RPC request."""
    jsonrpc: str = "2.0"
    method: Literal[Commands.HALT_ELECTION]
    params: HaltElectionParams
    id: str | int


class GetStatusRequest(BaseModel):
    """Schema validation for a Get Status RPC request."""
    jsonrpc: str = "2.0"
    method: Literal[Commands.GET_STATUS]
    params: GetStatusParams
    id: str | int


class GetStateRequest(BaseModel):
    """Schema validation for a Get State RPC request."""
    jsonrpc: str = "2.0"
    method: Literal[Commands.GET_STATE]
    params: GetStateParams
    id: str | int


class GetResultsRequest(BaseModel):
    """Schema validation for a Get Results RPC request."""
    jsonrpc: str = "2.0"
    method: Literal[Commands.GET_RESULTS]
    params: GetResultsParams
    id: str | int


class GetAuditLogsRequest(BaseModel):
    """Schema validation for a Get Audit Logs RPC request."""
    jsonrpc: str = "2.0"
    method: Literal[Commands.GET_AUDIT_LOGS]
    params: GetAuditLogsParams
    id: str | int


class RPCResponse(BaseModel):
    """Schema representing a successful JSON-RPC response."""
    jsonrpc: str = "2.0"
    result: dict[str, Any]
    id: str | int

    def to_json(self) -> str:
        """Serializes the response object to a JSON string."""
        return json.dumps(
            {"jsonrpc": self.jsonrpc, "result": self.result, "id": self.id}
        )


class RPCError(BaseModel):
    """Error payload containing the error code and message."""
    code: ErrorCode
    message: str


class RPCErrorResponse(BaseModel):
    """Schema representing a failed JSON-RPC response."""
    jsonrpc: str = "2.0"
    error: RPCError
    id: str | int | None


class RPCNotification(BaseModel):
    """Schema representing a JSON-RPC notification (no request ID)."""
    jsonrpc: str = "2.0"
    method: str
    params: dict[str, Any]


def success_response(request_id: str | int, result: dict[str, Any]) -> RPCResponse:
    """Helper to generate a successful RPCResponse object.

    Args:
        request_id: The request transaction ID.
        result: The execution result dictionary.

    Returns:
        An RPCResponse instance.
    """
    return RPCResponse(
        jsonrpc="2.0",
        result=result,
        id=request_id,
    )


def error_response(
    request_id: str | int | None,
    code: int,
    message: str,
) -> RPCErrorResponse:
    """Helper to generate a failed RPCErrorResponse object.

    Args:
        request_id: The request transaction ID.
        code: The error code.
        message: The descriptive error message.

    Returns:
        An RPCErrorResponse instance.
    """
    return RPCErrorResponse(
        jsonrpc="2.0",
        error=RPCError(code=code, message=message),
        id=request_id,
    )


def parse_request(request: str) -> RPCRequest:
    """Parses a raw JSON string into an RPCRequest validation model.

    Args:
        request: Raw JSON request string.

    Returns:
        An RPCRequest instance.
    """
    return RPCRequest(**json.loads(request))
