import logging
from dataclasses import replace
import pytest
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.belief import Belief
from cop_agent.domain.board import BoardState
from cop_agent.domain.rules import legal_moves
from cop_agent.domain.search import reachable, reachable_area
from cop_agent.strategy.barriers import (
    SELF_PENALTY,
    BarrierScore,
    best_placement,
    candidates,
    chain_progress,
    rank_placements,
    safe_placements,
    score_placement,
    winning_placement,
    wins_outright,
)
AXES = AxisConvention()
def board(cop: tuple[int, int], thief: tuple[int, int], **kw: object) -> BoardState:
    barriers = kw.get("barriers", frozenset())
    assert isinstance(barriers, frozenset | set)
    size = kw.get("grid_size", 7)
    assert isinstance(size, int)
    return BoardState(cop=cop, thief=thief, grid_size=size, barriers=frozenset(barriers))
