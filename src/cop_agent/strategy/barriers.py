"""Deciding which cell is worth a barrier."""

import logging

from ..domain.axes import AxisConvention
from ..domain.belief import Belief
from ..domain.board import BoardState, Position
from ._barriers_scoring import (
    SELF_PENALTY as SELF_PENALTY,
)
from ._barriers_scoring import (
    BarrierScore as BarrierScore,
)
from ._barriers_scoring import (
    candidates as candidates,
)
from ._barriers_scoring import (
    chain_progress as chain_progress,
)
from ._barriers_scoring import (
    score_placement as score_placement,
)
from ._barriers_scoring import (
    severed_mass as severed_mass,
)
from ._barriers_scoring import (
    still_reaches as still_reaches,
)
from ._barriers_scoring import (
    winning_placement as winning_placement,
)
from ._barriers_scoring import (
    wins_outright as wins_outright,
)

logger = logging.getLogger(__name__)


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
