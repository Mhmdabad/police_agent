"""Deciding which cell is worth a barrier.

Fourteen barriers, thirty-five turns. A placement also forfeits the cop's
movement for that turn, so every wall costs a step of pursuit as well as a
unit of a scarce resource — which makes "is this cell worth sealing" a question
with a real answer rather than a preference.

Three axes, in the order they matter:

**Escape-area reduction.** How many cells the thief can still reach after the
seal, compared with before. This is the only axis that measures the actual
objective. A barrier on open ground shaves off nothing and the flood fill says
so; one that closes a corridor takes a whole region.

**Chain progress.** A wall only encloses when it *lands on something* — an
existing barrier, or the board edge. Appendix D's arithmetic follows from this:
enclosure costs two barriers in a corner, three on an edge, four in the open,
because the corner supplies two sides for free. A cell whose neighbours are
already sealed or off-board is a cell where the next barrier finishes work
already paid for.

**Self-penalty.** The rules do not stop the cop walling *itself* off, and a
greedy sequence of locally excellent barriers will do exactly that. Sealing
here is scored against losing reach to the target. Issue #43 turns this into a
hard veto; at this stage it is a term, so the ranking stays comparable.
"""

import logging
from dataclasses import dataclass, replace

from ..domain.actions import placement_range
from ..domain.axes import AxisConvention
from ..domain.board import MOVES, BoardState, Position
from ..domain.rules import target_of
from ..domain.search import is_connected, reachable_area

logger = logging.getLogger(__name__)

SELF_PENALTY = 1000
"""Weight for cutting ourselves off. Large enough to dominate any real gain.

Not infinite: the score stays a number so candidates remain totally ordered
and the log shows *why* a placement lost rather than only that it was dropped.
"""


@dataclass(frozen=True, slots=True)
class BarrierScore:
    """One candidate placement, scored on all three axes.

    Kept as separate fields rather than a single total so the log can show the
    breakdown. A placement decision that cannot be explained after the fact is
    one we cannot debug from a match transcript.
    """

    at: Position
    escape_reduction: int
    chain: int
    disconnects: bool

    @property
    def total(self) -> int:
        """Higher is better. Chain progress breaks ties on equal reduction."""
        penalty = SELF_PENALTY if self.disconnects else 0
        return self.escape_reduction + self.chain - penalty

    def __str__(self) -> str:
        cut = " CUTS-SELF-OFF" if self.disconnects else ""
        return (
            f"{self.at} total={self.total} (escape-{self.escape_reduction} chain+{self.chain}){cut}"
        )


def chain_progress(state: BoardState, at: Position, axes: AxisConvention) -> int:
    """How many of ``at``'s four sides are already closed.

    Counts sealed neighbours and off-board sides alike, because they close a
    line equally well — that equivalence is what makes a corner cheaper to
    enclose than open ground, and it is the whole reason to herd toward edges.
    """
    closed = 0
    for move in MOVES:
        if move == "STAY":
            continue
        neighbour = target_of(at, move, axes)
        if not state.in_bounds(neighbour) or state.is_barrier(neighbour):
            closed += 1
    return closed


def still_reaches(sealed: BoardState, target: Position, axes: AxisConvention) -> bool:
    """Whether the cop can still get to ``target`` in this post-seal state.

    Not simply :func:`is_connected` from the cop's cell, because the cop may
    seal the cell it is standing on. A sealed origin has no reachable set, but
    the cop is not trapped by it: leaving asks whether the *destination* is
    free, so all four steps remain legal and only re-entry is lost. Reading
    that as "cut off" would put a permanent 1000-point penalty on a placement
    that is often the best wall available.
    """
    if sealed.is_free(sealed.cop):
        return is_connected(sealed, sealed.cop, target, axes)
    exits = (target_of(sealed.cop, move, axes) for move in MOVES if move != "STAY")
    return any(
        sealed.is_free(exit_cell) and is_connected(sealed, exit_cell, target, axes)
        for exit_cell in exits
    )


def score_placement(
    state: BoardState, at: Position, axes: AxisConvention, target: Position
) -> BarrierScore:
    """Score sealing ``at``, with the thief believed to be at ``target``."""
    sealed = replace(state, barriers=state.barriers | {at})
    before = reachable_area(state, target, axes)
    after = reachable_area(sealed, target, axes)
    return BarrierScore(
        at=at,
        escape_reduction=before - after,
        chain=chain_progress(state, at, axes),
        disconnects=not still_reaches(sealed, target, axes),
    )


def rank_placements(
    state: BoardState, axes: AxisConvention, target: Position
) -> list[BarrierScore]:
    """Every legal placement this turn, best first.

    Ties resolve by row then column, so two peers replaying the same match rank
    them identically. A ranking that depended on set iteration order would be
    reproducible on one machine and nowhere else.
    """
    candidates = sorted(cell for cell in placement_range(state, axes) if not state.is_barrier(cell))
    scored = [score_placement(state, cell, axes, target) for cell in candidates]
    scored.sort(key=lambda score: (-score.total, score.at))
    if scored:
        logger.info(
            "barrier candidates from cop=%s target=%s: %s",
            state.cop,
            target,
            "; ".join(str(score) for score in scored),
        )
    else:
        logger.info("no barrier candidates from cop=%s: every cell in reach is sealed", state.cop)
    return scored


def best_placement(
    state: BoardState, axes: AxisConvention, target: Position
) -> BarrierScore | None:
    """The highest-scoring placement, or ``None`` if nothing is available."""
    ranked = rank_placements(state, axes, target)
    return ranked[0] if ranked else None
