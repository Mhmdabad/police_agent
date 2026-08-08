import logging
import pytest
from cop_agent.domain.actions import DEFAULT_MAX_BARRIERS, MoveAction, PlaceBarrier
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.strategy.barriers import BarrierScore
from cop_agent.strategy.budget import RESERVE, Budget
from cop_agent.strategy.police_brain import PoliceBrain
from cop_agent.strategy.tradeoff import Tradeoff, distance_closed, weigh
AXES = AxisConvention()
CORRIDOR = frozenset({(0, 2), (1, 2), (3, 2), (4, 2), (5, 2), (6, 2)})
def board(**kw: object) -> BoardState:
    cop = kw.get("cop", (0, 0))
    thief = kw.get("thief", (3, 3))
    barriers = kw.get("barriers", frozenset())
    assert isinstance(cop, tuple) and isinstance(thief, tuple)
    assert isinstance(barriers, frozenset | set)
    return BoardState(cop=cop, thief=thief, grid_size=7, barriers=frozenset(barriers))
GOOD_PLACEMENT = BarrierScore(at=(1, 1), escape_reduction=5, chain=0, disconnects=False)
def call(
    placement: BarrierScore | None = GOOD_PLACEMENT,
    move_gain: int = 1,
    required: int = 1,
    used: int = 0,
    endgame: bool = False,
) -> Tradeoff:
    return Tradeoff(
        placement=placement,
        move_gain=move_gain,
        required=required,
        budget=Budget(used=used),
        endgame=endgame,
    )
