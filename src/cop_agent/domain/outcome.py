"""How a sub-game ends.

Termination is decided from board state, never from either side's assertion.
A Capture Claim binds the cop as much as the thief: it must be derivable from
verified board state, and a false claim is exposed at the log audit and
disqualifies the team outright with no appeal. The claim is therefore computed
here, directly from the state, so that no code path exists which could assert a
capture the board does not show.
"""

from enum import Enum

from ..shared.appendix_f import book_int
from .axes import AxisConvention
from .board import BoardState, Position
from .rules import blocked_neighbours


def is_capture_by_overlap(state: BoardState) -> bool:
    """Whether the cop occupies the thief's cell.

    The primary capture condition: the cop lands on the thief and issues a
    Capture Claim. Derived from position alone, so a claim can be checked
    against the state rather than trusted.
    """
    return state.cop == state.thief


def is_trapping_capture(state: BoardState) -> bool:
    """Whether the thief stands on a sealed cell.

    The cop may place a barrier on the cell the thief occupies, and that
    counts as a capture. This is the only way the condition can arise: a
    thief can never *move* onto a barrier, so a thief standing on one was
    sealed in place.

    It is also the reason ``BoardState`` deliberately does not enforce
    "the thief is never on a barrier" — that invariant would make this win
    condition unrepresentable.
    """
    return state.is_barrier(state.thief)


def is_enclosure_capture(state: BoardState, axes: AxisConvention) -> bool:
    """Whether the thief is walled in with nowhere to step.

    The rulebook: *"a thief imprisoned with no legal move at all (all adjacent
    cells blocked by barriers and/or board edges) is likewise considered
    captured."*

    Read literally, "no legal move at all" would never occur, because ``STAY``
    survives any encirclement. The parenthetical settles it: the condition is
    defined over the four **adjacent** cells, so standing still is not an
    escape. Board edges count as walls, which is why a cornered thief needs
    only two barriers rather than four.
    """
    return blocked_neighbours(state, state.thief, axes) == 4


DEFAULT_SURVIVAL_THRESHOLD: int = book_int("movement_and_barriers", "survival_threshold")
"""Appendix F survival threshold. A *minimum*: raisable by agreement only."""


def is_survival(
    state: BoardState,
    axes: AxisConvention,
    survival_threshold: int = DEFAULT_SURVIVAL_THRESHOLD,
) -> bool:
    """Whether the thief has outlasted the clock.

    This agent's win condition: surviving ``survival_threshold`` valid steps
    without being captured. A *step* is a full turn — both sides having moved —
    which is why :func:`~.rules.advance_turn` is separate from applying a move.
    Counting half-moves would reach the threshold in half the required turns and
    claim a win the thief had not earned.

    Survival is only reached if no capture has fired, so the capture conditions
    are checked here rather than left to the caller to remember.
    """
    if is_capture_by_overlap(state) or is_trapping_capture(state):
        return False
    if is_enclosure_capture(state, axes):
        return False
    return state.step >= survival_threshold


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


def capture_claim(state: BoardState, axes: AxisConvention) -> Position | None:
    """The cell to claim capture on, or ``None``. **The only emitter.**

    A Capture Claim binds the cop as much as the thief. It has to be derivable
    from verified board state, and a false one is exposed at the log audit and
    disqualifies the team outright with no appeal — a harsher penalty than
    losing every match in the series.

    So there is exactly one function that can produce a claim, it takes the
    board and nothing else, and it has no argument that could express *wanting*
    to claim. A policy cannot pass a flag; a brain cannot pass a preference.
    The only way to obtain a claim is to be in a position that already is one.

    Returned as the thief's cell rather than as a boolean, because a claim has
    to say **where**: the opponent verifies it against their own board, and
    "I captured you" is not checkable while "I captured you at (3,4)" is.
    """
    if is_capture_by_overlap(state) or is_trapping_capture(state):
        return state.thief
    if is_enclosure_capture(state, axes):
        return state.thief
    return None


def claim_is_supported(state: BoardState, axes: AxisConvention, at: Position) -> bool:
    """Whether a claim at ``at`` is one this board actually shows.

    Used on the receiving side, against the opponent's claim, and on ours
    before sending. Both directions matter and for opposite reasons: theirs may
    be false, and ours may be right about the capture and wrong about the cell.
    """
    return capture_claim(state, axes) == at
