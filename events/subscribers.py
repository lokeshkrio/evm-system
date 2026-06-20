import json
from collections import Counter

from events.event_types import DomainEvent, VoteCastEvent
from server.connection_manager import ConnectionManager
from services.audit_service import AuditEvent, AuditService
from services.backup_service import BackupService


class AuditSubscriber:
    def __init__(self, audit: AuditService) -> None:
        self.audit = audit

    async def __call__(self, event: DomainEvent) -> None:
        await self.audit.log_event(AuditEvent(event.event_type), event.details)


class MetricsSubscriber:
    def __init__(self, metrics_service: Any) -> None:
        self.metrics_service = metrics_service
        self.event_counts: Counter[str] = Counter()

    async def __call__(self, event: DomainEvent) -> None:
        self.event_counts[event.event_type] += 1
        if isinstance(event, VoteCastEvent):
            self.metrics_service.record_vote()


class WebSocketSubscriber:
    def __init__(self, connections: ConnectionManager) -> None:
        self.connections = connections

    async def __call__(self, event: DomainEvent) -> None:
        # Ballot details belong in the audit chain, not client notifications.
        public_details = {
            key: value
            for key, value in event.details.items()
            if key in {"state", "from_state", "to_state"}
        }
        notification = {
            "jsonrpc": "2.0",
            "method": event.event_type.lower(),
            "params": {
                **public_details,
                "timestamp": event.timestamp,
            },
        }
        await self.connections.broadcast(json.dumps(notification))


class BackupSubscriber:
    def __init__(self, backup_service: BackupService) -> None:
        self.backup_service = backup_service

    async def __call__(self, event: DomainEvent) -> None:
        # Trigger backup on major state changes
        if event.event_type in {
            "ELECTION_STARTED",
            "ELECTION_STOPPED",
            "ELECTION_HALTED",
            "ELECTION_RESUMED"
        }:
            await self.backup_service.export_snapshot("snapshot.json")
