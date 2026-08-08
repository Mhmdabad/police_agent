import random
from dataclasses import replace
import pytest
from cop_agent.domain.actions import (
    DEFAULT_MAX_BARRIERS,
    MoveAction,
    PlaceBarrier,
    apply_action,
    placement_range,
)
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import MOVES, BoardState
from cop_agent.domain.outcome import is_capture_by_overlap, is_trapping_capture
from cop_agent.domain.rules import legal_moves, target_of
from cop_agent.domain.scoring import Outcome, evaluate
from cop_agent.strategy.barriers import best_placement, rank_placements, safe_placements
from cop_agent.strategy.base import NoLegalActionError
from cop_agent.strategy.budget import RESERVE, Budget, looks_like_endgame
from cop_agent.strategy.police_brain import PoliceBrain
AXES = AxisConvention()
def make(**kw: object) -> BoardState:
    cop = kw.get("cop", (0, 0))
    thief = kw.get("thief", (3, 3))
    barriers = kw.get("barriers", frozenset())
    step = kw.get("step", 0)
    assert isinstance(cop, tuple) and isinstance(thief, tuple)
    assert isinstance(barriers, frozenset | set) and isinstance(step, int)
    return BoardState(cop=cop, thief=thief, grid_size=7, barriers=frozenset(barriers), step=step)
def evade(state: BoardState) -> BoardState:
    options = legal_moves(state, "thief", AXES)
    if not options:
        return state
    best = max(
        options,
        key=lambda move: (
            abs(target_of(state.thief, move, AXES)[0] - state.cop[0])
            + abs(target_of(state.thief, move, AXES)[1] - state.cop[1]),
            -MOVES.index(move),
        ),
    )
    return replace(state, thief=target_of(state.thief, best, AXES))
