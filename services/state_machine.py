from models.enums import ElectionState


class ElectionStateMachine:
    """Stateless policy for explicit election lifecycle transitions."""

    @staticmethod
    def start_election(current: ElectionState) -> ElectionState | None:
        if current != ElectionState.INITIALIZED:
            return None
        return ElectionState.STARTED

    @staticmethod
    def enable_vote(current: ElectionState) -> ElectionState | None:
        if current != ElectionState.STARTED:
            return None
        return ElectionState.VOTING

    @staticmethod
    def vote_casted(current: ElectionState) -> ElectionState | None:
        if current != ElectionState.VOTING:
            return None
        return ElectionState.STARTED

    @staticmethod
    def halt(current: ElectionState) -> ElectionState | None:
        if current != ElectionState.VOTING:
            return None
        return ElectionState.HALTED

    @staticmethod
    def resume(current: ElectionState) -> ElectionState | None:
        if current != ElectionState.HALTED:
            return None
        return ElectionState.STARTED

    @staticmethod
    def end(current: ElectionState) -> ElectionState | None:
        if current not in (ElectionState.STARTED, ElectionState.HALTED):
            return None
        return ElectionState.ENDED

    @staticmethod
    def reset(current: ElectionState) -> ElectionState | None:
        if current != ElectionState.ENDED:
            return None
        return ElectionState.INITIALIZED
