"""Helper functions and dataclasses for barrier placement scoring and evaluation."""

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


@dataclass(frozen=True, slots=True)
class BarrierScore:
    """One candidate placement, scored on all three axes."""

    at: Position
    escape_reduction: int
    chain: int
    disconnects: bool
    immobilises: bool = False
    severed_belief: float | None = None

    @property
    def permitted(self) -> bool:
        return not (self.disconnects or self.immobilises)

    @property
    def value(self) -> float:
        if self.severed_belief is None:
            return float(self.escape_reduction)
        return self.escape_reduction * self.severed_belief

    @property
    def total(self) -> float:
        penalty = 0 if self.permitted else SELF_PENALTY
        return self.value + self.chain - penalty

    @property
    def veto(self) -> str:
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
    return sorted(cell for cell in placement_range(state, axes) if not state.is_barrier(cell))


def wins_outright(state: BoardState, at: Position, axes: AxisConvention) -> bool:
    sealed = replace(state, barriers=state.barriers | {at})
    return is_trapping_capture(sealed) or is_enclosure_capture(sealed, axes)


def winning_placement(
    state: BoardState, axes: AxisConvention, max_barriers: int = DEFAULT_MAX_BARRIERS
) -> Position | None:
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
    closed = 0
    for move in MOVES:
        if move == "STAY":
            continue
        neighbour = target_of(at, move, axes)
        if not state.in_bounds(neighbour) or state.is_barrier(neighbour):
            closed += 1
    return closed


def still_reaches(sealed: BoardState, target: Position, axes: AxisConvention) -> bool:
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
    lost = reachable(state, target, axes) - reachable(sealed, target, axes)
    return sum(belief.at(cell) for cell in lost | {at})


def score_placement(
    state: BoardState,
    at: Position,
    axes: AxisConvention,
    target: Position,
    belief: Belief | None = None,
) -> BarrierScore:
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
