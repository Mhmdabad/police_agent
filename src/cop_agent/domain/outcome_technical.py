"""How a sub-game is voided rather than won.

Split out of :mod:`.outcome` so that module keeps to the file-length budget.
The board-derived termination conditions and the Capture Claim stay there;
what lives here is the other way a sub-game can end — one nobody wins.

:mod:`.outcome` re-exports both names, so ``domain.outcome`` remains the single
import site for termination.
"""

from enum import Enum


class TechnicalLoss(Enum):
    """Why a sub-game was voided.

    A technical loss scores **zero for both sides**, regardless of the board.
    That symmetry is deliberate: it removes any incentive to win by stalling,
    and it means a dropped tunnel destroys a winning position just as surely as
    a losing one. Protocol hygiene is therefore worth more than any single
    board advantage.
    """

    CRASH = "crash"
    """A peer stopped responding or exited unexpectedly."""

    TIMEOUT = "timeout"
    """A deadline expired. A missed deadline is a failure, not a reason to wait."""

    FORGERY = "forgery"
    """A commitment did not match its reveal. Proven tampering, no appeal."""

    ILLEGAL_ACTION = "illegal_action"
    """An action violated the physics both peers enforce."""


def technical_loss_scores() -> tuple[int, int]:
    """Points awarded on a technical loss, as ``(cop, thief)``.

    Zero for both. Not a parameter: Appendix F marks it **fixed**, and
    deviating from a fixed value disqualifies the team.
    """
    return (0, 0)
