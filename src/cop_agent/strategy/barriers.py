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

**Self-cost.** The rules do not stop the cop walling *itself* off, and a
greedy sequence of locally excellent barriers will do exactly that.

That last axis is a **hard constraint**, not a weight. Two placements are
refused outright however well they score: one that cuts the cop off from the
region it is hunting, and one that leaves the cop with no legal move at all.
The second is the more expensive mistake. A cop that cannot move cannot answer
its turn, and an unanswered turn is a technical loss — which scores **zero for
both sides**, converting a game we were winning into a game nobody played.

Refused candidates are still scored and still logged. Dropping them silently
would leave a match transcript showing a barrier that went somewhere odd with
no record of what was rejected or why.
"""

import logging
from dataclasses import dataclass, replace

from ..domain.actions import placement_range
from ..domain.axes import AxisConvention
from ..domain.board import MOVES, BoardState, Position
from ..domain.rules import legal_moves, target_of
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
    immobilises: bool = False

    @property
    def permitted(self) -> bool:
        """Whether the self-preservation constraint allows this placement.

        A hard gate, checked before the score is consulted at all. No escape
        reduction is worth being unable to reach the thief, and none is worth
        being unable to answer a turn.
        """
        return not (self.disconnects or self.immobilises)

    @property
    def total(self) -> int:
        """Higher is better. Chain progress breaks ties on equal reduction.

        Refused candidates keep a number rather than becoming incomparable, so
        the log can show how good the placement we turned down would have been.
        """
        penalty = 0 if self.permitted else SELF_PENALTY
        return self.escape_reduction + self.chain - penalty

    @property
    def veto(self) -> str:
        """Why this placement is refused, or the empty string if it is not."""
        if self.immobilises:
            return "NO-LEGAL-MOVE-AFTER"
        if self.disconnects:
            return "CUTS-SELF-OFF"
        return ""

    def __str__(self) -> str:
        refused = f" {self.veto}" if self.veto else ""
        return (
            f"{self.at} total={self.total} "
            f"(escape-{self.escape_reduction} chain+{self.chain}){refused}"
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
        immobilises=not legal_moves(sealed, "cop", axes),
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


def safe_placements(
    state: BoardState, axes: AxisConvention, target: Position
) -> list[BarrierScore]:
    """Ranked placements with the refused ones removed.

    The filter is separate from the ranking so that both survive: callers get
    only permitted placements, and the log still records what was rejected.
    """
    permitted = [score for score in rank_placements(state, axes, target) if score.permitted]
    if not permitted:
        logger.info("no permitted placement from cop=%s: every candidate is refused", state.cop)
    return permitted


def best_placement(
    state: BoardState, axes: AxisConvention, target: Position
) -> BarrierScore | None:
    """The best placement the constraint allows, or ``None`` if there is none.

    ``None`` means *do not place a barrier this turn*, never "place the least
    bad one". Not placing costs a barrier we keep; placing a refused one can
    cost the match.
    """
    permitted = safe_placements(state, axes, target)
    return permitted[0] if permitted else None
