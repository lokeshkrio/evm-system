from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, ClassVar


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class DomainEvent:
    details: dict[str, Any]
    timestamp: str = field(default_factory=utc_timestamp)
    event_type: ClassVar[str] = "DOMAIN_EVENT"


class ElectionStartedEvent(DomainEvent):
    event_type = "ELECTION_STARTED"


class VotingEnabledEvent(DomainEvent):
    event_type = "VOTING_ENABLED"


class VoteCastEvent(DomainEvent):
    event_type = "VOTE_CAST"


class DuplicateVoteEvent(DomainEvent):
    event_type = "DUPLICATE_VOTE"


class ElectionHaltedEvent(DomainEvent):
    event_type = "ELECTION_HALTED"


class ElectionResumedEvent(DomainEvent):
    event_type = "ELECTION_RESUMED"


class ElectionStoppedEvent(DomainEvent):
    event_type = "ELECTION_STOPPED"


class ElectionRecoveredEvent(DomainEvent):
    event_type = "ELECTION_RECOVERED"
