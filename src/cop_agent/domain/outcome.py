"""How a sub-game ends.

Termination is decided from board state, never from either side's assertion.
A Capture Claim binds the cop as much as the thief: it must be derivable from
verified board state, and a false claim is exposed at the log audit and
disqualifies the team outright with no appeal. The claim is therefore computed
here, directly from the state, so that no code path exists which could assert a
capture the board does not show.
"""

from .board import BoardState


def is_capture_by_overlap(state: BoardState) -> bool:
    """Whether the cop occupies the thief's cell.

    The primary capture condition: the cop lands on the thief and issues a
    Capture Claim. Derived from position alone, so a claim can be checked
    against the state rather than trusted.
    """
    return state.cop == state.thief
