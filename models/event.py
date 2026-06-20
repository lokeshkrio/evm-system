from dataclasses import dataclass


@dataclass(slots=True)
class Event:
    """Represents an audit/log event in the system for tracking election activities.

    Attributes:
        event_id: Auto-incrementing unique sequence number for auditing ordering.
        event_type: The type/category of the event (e.g., 'election_started').
        payload: JSON-structured additional metadata related to the event.
        timestamp: ISO 8601 formatted string of when the event occurred.
    """
    event_id: int
    event_type: str
    payload: dict
    timestamp: str