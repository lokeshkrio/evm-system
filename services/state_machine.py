import logging
from datetime import UTC, datetime
from models import enums

logger = logging.getLogger(__name__)


class ElectionStateMachine:
    """A finite state machine managing allowed transitions in the election lifecycle.

    States transition in a controlled manner:
    INITIALIZED -> STARTED -> VOTING -> ENDED/HALTED
    """

    def __init__(self) -> None:
        """Initializes the state machine to the INITIALIZED state."""
        self._state = enums.ElectionState.INITIALIZED

    @property
    def state(self) -> enums.ElectionState:
        """Gets the current ElectionState enum value."""
        return self._state

    @property
    def vote_count(self) -> int:
        """Placeholder for vote count (unimplemented)."""
        return 0

    def advance_state(self) -> bool:
        """Advances the election to the next logical state.

        Returns:
            True if the state was advanced successfully, False otherwise.
        """
        if self._state == enums.ElectionState.INITIALIZED:
            self._state = enums.ElectionState.STARTED
            logger.info(f"[{datetime.now(UTC)}] Election state advanced to: STARTED")
        elif self._state == enums.ElectionState.STARTED:
            self._state = enums.ElectionState.VOTING
            logger.info(f"[{datetime.now(UTC)}] Election state advanced to: VOTING")
        elif self._state == enums.ElectionState.VOTING:
            self._state = enums.ElectionState.STARTED
            logger.info(f"[{datetime.now(UTC)}] Election state advanced to: STARTED")
        elif self._state == enums.ElectionState.HALTED:
            self._state = enums.ElectionState.STARTED
            logger.info(f"[{datetime.now(UTC)}] Election state advanced to: STARTED")

        return True

    def halt(self) -> bool:
        """Halts the voting process if currently in the VOTING state.

        Returns:
            True if halted successfully, False otherwise.
        """
        if self._state == enums.ElectionState.VOTING:
            self._state = enums.ElectionState.HALTED
            logger.warning(f"[{datetime.now(UTC)}] Election state advanced to: HALTED")
            return True
        else:
            return False

    def end(self) -> bool:
        """Ends the voting process if currently in the VOTING state.

        Returns:
            True if ended successfully, False otherwise.
        """
        if self._state == enums.ElectionState.VOTING:
            self._state = enums.ElectionState.ENDED
            logger.info(f"[{datetime.now(UTC)}] Election state advanced to: ENDED")
            return True
        else:
            return False

    def restart(self) -> bool:
        """Restarts the election process if it has already ended.

        Returns:
            True if restarted successfully, False otherwise.
        """
        if self._state == enums.ElectionState.ENDED:
            self._state = enums.ElectionState.STARTED
            logger.warning(f"[{datetime.now(UTC)}] Election state advanced to: STARTED")
            return True
        else:
            return False
