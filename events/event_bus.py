import asyncio
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable

from events.event_types import DomainEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[[DomainEvent], Awaitable[None]]


class EventBus:
    """Publishes committed domain events to asynchronous subscribers."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        handlers = [
            *self._subscribers.get(event.event_type, ()),
            *self._subscribers.get("*", ()),
        ]
        if not handlers:
            return

        results = await asyncio.gather(
            *(handler(event) for handler in handlers),
            return_exceptions=True,
        )
        for handler, result in zip(handlers, results, strict=True):
            if isinstance(result, BaseException):
                logger.error(
                    "Event subscriber %r failed for %s",
                    handler,
                    event.event_type,
                    exc_info=(type(result), result, result.__traceback__),
                )
