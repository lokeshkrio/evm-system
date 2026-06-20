import time
from typing import Any

from server.connection_manager import ConnectionManager


class MetricsService:
    """Service to track and report application metrics."""

    def __init__(self, connection_manager: ConnectionManager) -> None:
        self.start_time = time.time()
        self.connection_manager = connection_manager
        self.votes_cast = 0
        self.rpc_calls = 0
        self.failed_requests = 0
        self.total_latency_ms = 0.0

    def record_vote(self) -> None:
        self.votes_cast += 1

    def record_rpc_call(self, latency_ms: float, success: bool) -> None:
        self.rpc_calls += 1
        self.total_latency_ms += latency_ms
        if not success:
            self.failed_requests += 1

    async def get_metrics(self) -> dict[str, Any]:
        uptime = time.time() - self.start_time
        avg_latency = (self.total_latency_ms / self.rpc_calls) if self.rpc_calls > 0 else 0.0
        return {
            "uptime_seconds": round(uptime, 2),
            "active_connections": len(self.connection_manager.active_connections),
            "votes_cast": self.votes_cast,
            "rpc_calls": self.rpc_calls,
            "failed_requests": self.failed_requests,
            "average_latency_ms": round(avg_latency, 2),
        }
