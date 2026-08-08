import random
import tomllib
from pathlib import Path
from typing import Any
import pytest
from cop_agent.domain.actions import (
    IllegalActionError,
    MoveAction,
    PlaceBarrier,
    place_barrier,
    placement_range,
)
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import MOVES, Agent, BoardState, Move
from cop_agent.domain.outcome import is_capture_by_overlap
from cop_agent.domain.rules import legal_moves, target_of
from cop_agent.domain.search import reachable_area
from cop_agent.strategy.barriers import winning_placement
from cop_agent.strategy.base import BrainBase, Decision, NoLegalActionError
from cop_agent.strategy.loader import DEFAULT_BRAIN, StrategyError, load_brain
from cop_agent.strategy.police_brain import PoliceBrain, manhattan
from cop_agent.strategy.tradeoff import weigh
AXES = AxisConvention()
def make(**kw: object) -> BoardState:
    base: dict[str, object] = {"grid_size": 7, "cop": (0, 0), "thief": (3, 3)}
    base.update(kw)
    return BoardState(**base)  # type: ignore[arg-type]
