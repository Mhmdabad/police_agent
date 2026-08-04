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

Once a belief map exists the reduction is **weighted by the probability the
thief is in the region being cut off**. Area alone counts cells; what the cop
is buying is the chance the thief is standing in them. Sealing a large empty
region spends one of fourteen barriers and a full turn of pursuit to remove
somewhere the thief demonstrably is not — and on a board with a live belief
map, the largest regions are frequently the emptiest, because that is where
the evidence has already ruled the thief out.

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

**One placement can end the match**, and that case is checked before any of
the above. A barrier on the thief's own cell is a trapping capture; a barrier
closing its last open side is an enclosure capture. Both are worth twenty
points outright, and both are easy to walk straight past while minimising
distance — the winning cell frequently scores *worse* on escape reduction than
its neighbours, because there is barely any escape left to reduce.
"""

import logging
from dataclasses import dataclass, replace

from ..domain.actions import DEFAULT_MAX_BARRIERS, placement_range
from ..domain.axes import AxisConvention
from ..domain.belief import Belief
from ..domain.board import MOVES, BoardState, Position
from ..domain.outcome import (
    is_capture_by_overlap,
    is_enclosure_capture,
    is_trapping_capture,
)
from ..domain.rules import legal_moves, target_of
from ..domain.search import is_connected, reachable, reachable_area

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
    severed_belief: float | None = None
    """Probability mass the seal removes, or ``None`` before belief exists."""

    @property
    def permitted(self) -> bool:
        """Whether the self-preservation constraint allows this placement.

        A hard gate, checked before the score is consulted at all. No escape
        reduction is worth being unable to reach the thief, and none is worth
        being unable to answer a turn.
        """
        return not (self.disconnects or self.immobilises)

    @property
    def value(self) -> float:
        """Escape reduction, weighted by belief when a belief map exists.

        Cells are what the flood fill counts; probability is what the barrier
        buys. A region twice the size but a tenth as likely is worth a fifth
        as much, and on a board with a live belief map the largest regions are
        frequently the emptiest — that is where evidence has already ruled the
        thief out.
        """
        if self.severed_belief is None:
            return float(self.escape_reduction)
        return self.escape_reduction * self.severed_belief

    @property
    def total(self) -> float:
        """Higher is better. Chain progress breaks ties on equal value.

        Refused candidates keep a number rather than becoming incomparable, so
        the log can show how good the placement we turned down would have been.
        """
        penalty = 0 if self.permitted else SELF_PENALTY
        return self.value + self.chain - penalty

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
        mass = "" if self.severed_belief is None else f" belief-{self.severed_belief:.0%}"
        return (
            f"{self.at} total={self.total:g} "
            f"(escape-{self.escape_reduction}{mass} chain+{self.chain}){refused}"
        )


def candidates(state: BoardState, axes: AxisConvention) -> list[Position]:
    """Cells the cop may seal this turn, in a stable order.

    Sorted before anything reads them: :func:`placement_range` returns a
    ``frozenset``, and a decision that leaned on set iteration order would be
    reproducible on one machine and nowhere else.
    """
    return sorted(cell for cell in placement_range(state, axes) if not state.is_barrier(cell))


def wins_outright(state: BoardState, at: Position, axes: AxisConvention) -> bool:
    """Whether sealing ``at`` ends the match in our favour this turn.

    Both terminal conditions a barrier can produce, asked of the resulting
    state rather than pattern-matched: a thief standing on a sealed cell, or
    a thief whose four adjacent cells are all closed. Deriving the answer from
    :mod:`..domain.outcome` is deliberate — a Capture Claim must be checkable
    against the board by the opponent, and a claim this module reasoned its
    way to independently is a claim that can disagree with the referee we
    both have to accept.
    """
    sealed = replace(state, barriers=state.barriers | {at})
    return is_trapping_capture(sealed) or is_enclosure_capture(sealed, axes)


def winning_placement(
    state: BoardState, axes: AxisConvention, max_barriers: int = DEFAULT_MAX_BARRIERS
) -> Position | None:
    """A placement that wins outright this turn, if one is legally available.

    Checked before the value scorer and before the self-preservation gate,
    because neither is meaningful once the match is over. A barrier that walls
    us in permanently is fine if the game ends on the same turn.

    Returns ``None`` when the quota is spent: a win that cannot be paid for is
    not a win, and the caller must fall through to ordinary play.

    Also ``None`` when the state is *already* terminal. Without that guard a
    thief standing on a barrier makes :func:`is_trapping_capture` true of
    every resulting state, so the first candidate examined would be returned
    as the winning cell — and a Capture Claim naming a barrier that had
    nothing to do with the capture is a false claim, which disqualifies the
    team at audit. The orchestrator should never ask for an action in a
    finished position, but "should never" is not a guarantee worth a match.
    """
    if state.barriers_used >= max_barriers:
        return None
    if is_trapping_capture(state) or is_capture_by_overlap(state):
        return None
    for cell in candidates(state, axes):
        if wins_outright(state, cell, axes):
            logger.info("winning placement at %s from cop=%s", cell, state.cop)
            return cell
    return None


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


def severed_mass(
    state: BoardState,
    sealed: BoardState,
    at: Position,
    axes: AxisConvention,
    target: Position,
    belief: Belief,
) -> float:
    """Belief carried by the cells the seal removes from the thief's reach.

    The cells lost are those reachable before and not after, plus the sealed
    cell itself — a barrier on the thief's own most-likely square removes that
    square's mass even though it was never "cut off" from anything. Summing
    belief over exactly those cells answers what the wall is actually buying.
    """
    lost = reachable(state, target, axes) - reachable(sealed, target, axes)
    return sum(belief.at(cell) for cell in lost | {at})


def score_placement(
    state: BoardState,
    at: Position,
    axes: AxisConvention,
    target: Position,
    belief: Belief | None = None,
) -> BarrierScore:
    """Score sealing ``at``, with the thief believed to be at ``target``.

    ``belief`` weights the reduction by the probability the thief is in the
    region being removed. Omitting it keeps the raw cell count, which is the
    correct reading before a belief map exists — a uniform belief would scale
    every candidate identically and change no ranking anyway.
    """
    sealed = replace(state, barriers=state.barriers | {at})
    before = reachable_area(state, target, axes)
    after = reachable_area(sealed, target, axes)
    reduction = before - after
    weight = severed_mass(state, sealed, at, axes, target, belief) if belief else None
    return BarrierScore(
        at=at,
        escape_reduction=reduction,
        chain=chain_progress(state, at, axes),
        disconnects=not still_reaches(sealed, target, axes),
        immobilises=not legal_moves(sealed, "cop", axes),
        severed_belief=weight,
    )


def rank_placements(
    state: BoardState, axes: AxisConvention, target: Position, belief: Belief | None = None
) -> list[BarrierScore]:
    """Every legal placement this turn, best first.

    Ties resolve by row then column, so two peers replaying the same match rank
    them identically. A ranking that depended on set iteration order would be
    reproducible on one machine and nowhere else.
    """
    scored = [
        score_placement(state, cell, axes, target, belief) for cell in candidates(state, axes)
    ]
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
    state: BoardState, axes: AxisConvention, target: Position, belief: Belief | None = None
) -> list[BarrierScore]:
    """Ranked placements with the refused ones removed.

    The filter is separate from the ranking so that both survive: callers get
    only permitted placements, and the log still records what was rejected.
    """
    permitted = [score for score in rank_placements(state, axes, target, belief) if score.permitted]
    if not permitted:
        logger.info("no permitted placement from cop=%s: every candidate is refused", state.cop)
    return permitted


def best_placement(
    state: BoardState, axes: AxisConvention, target: Position, belief: Belief | None = None
) -> BarrierScore | None:
    """The best placement the constraint allows, or ``None`` if there is none.

    ``None`` means *do not place a barrier this turn*, never "place the least
    bad one". Not placing costs a barrier we keep; placing a refused one can
    cost the match.
    """
    permitted = safe_placements(state, axes, target, belief)
    return permitted[0] if permitted else None
