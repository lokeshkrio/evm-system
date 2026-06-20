# services/state_machine.py

import logging
from datetime import UTC, datetime

from models.enums import ElectionState

logger = logging.getLogger(__name__)


class ElectionStateMachine:
    """
    Election lifecycle:

    INITIALIZED
        ↓
    STARTED
        ↓
    VOTING
        ↓
    STARTED
        ↓
    ...
        ↓
    HALTED
        ↓
    STARTED
        ↓
    ENDED
    """

    def __init__(
        self,
        initial_state: ElectionState = ElectionState.INITIALIZED,
    ) -> None:
        self._state = initial_state

    @property
    def state(self) -> ElectionState:
        return self._state

    def _transition(
        self,
        new_state: ElectionState,
    ) -> None:

        old_state = self._state

        self._state = new_state

        logger.info(
            "[%s] Election state changed: %s -> %s",
            datetime.now(UTC).isoformat(),
            old_state.value,
            new_state.value,
        )

    def restore(self, state: ElectionState) -> None:
        """Restore a validated state after persistence recovery or rollback."""
        old_state = self._state
        self._state = state
        logger.warning(
            "[%s] Election state restored: %s -> %s",
            datetime.now(UTC).isoformat(),
            old_state.value,
            state.value,
        )

    def start_election(self) -> bool:
        """
        INITIALIZED -> STARTED
        """

        if self._state != ElectionState.INITIALIZED:
            return False

        self._transition(ElectionState.STARTED)

        return True

    def enable_vote(self) -> bool:
        """
        STARTED -> VOTING
        """

        if self._state != ElectionState.STARTED:
            return False

        self._transition(ElectionState.VOTING)

        return True

    def vote_casted(self) -> bool:
        """
        VOTING -> STARTED
        """

        if self._state != ElectionState.VOTING:
            return False

        self._transition(ElectionState.STARTED)

        return True

    def halt(self) -> bool:
        """
        VOTING -> HALTED
        """

        if self._state != ElectionState.VOTING:
            return False

        self._transition(ElectionState.HALTED)

        return True

    def resume(self) -> bool:
        """
        HALTED -> STARTED
        """

        if self._state != ElectionState.HALTED:
            return False

        self._transition(ElectionState.STARTED)

        return True

    def end(self) -> bool:
        """
        STARTED/HALTED -> ENDED
        """

        if self._state not in (
            ElectionState.STARTED,
            ElectionState.HALTED,
        ):
            return False

        self._transition(ElectionState.ENDED)

        return True

    def reset(self) -> bool:
        """
        ENDED -> INITIALIZED
        """

        if self._state != ElectionState.ENDED:
            return False

        self._transition(ElectionState.INITIALIZED)

        return True
