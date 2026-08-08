import dataclasses
import typing
import pytest
from cop_agent.domain.actions import (
    DEFAULT_MAX_BARRIERS,
    Action,
    IllegalActionError,
    MoveAction,
    PlaceBarrier,
    apply_action,
    place_barrier,
    placement_range,
)
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.domain.rules import IllegalMoveError, legal_moves
AXES = AxisConvention()
def make(**kw: object) -> BoardState:
    base: dict[str, object] = {"grid_size": 7, "cop": (0, 0), "thief": (3, 3)}
    base.update(kw)
    return BoardState(**base)  # type: ignore[arg-type]
