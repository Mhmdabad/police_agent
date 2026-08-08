import math
from typing import Any
import pytest
from cop_agent.domain.actions import MoveAction, PlaceBarrier
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.domain.crypto import commit_of, step_record
from cop_agent.domain.memory import ScentMemory
from cop_agent.domain.scent import CENTRE_INTENSITY, emission
from cop_agent.domain.scent_audit import (
    ScentFieldError,
    StepPlay,
    audit_scent,
    check_field,
    replay,
    trail_snapshots,
)
from cop_agent.domain.trail import RETENTION, Trail
AXES = AxisConvention()
BOARD = 8
OUR_ROLE = "police"
OUR_START = (0, 0)
THEIR_START = (6, 5)
THEIR_MOVES = ["N", "W", "STAY"]
"""Three moves the opponent may legally play from :data:`THEIR_START`."""
OUR_STEP = ["STAY", "S"]
"""Our own two moves for the replay below."""
EXPECTED_REPLAY = [((0, 0), (5, 5)), ((1, 0), (5, 4))]
"""Where each side stands after those two turns.
Written out rather than computed: an expectation derived from the module under
test is a restatement of it.
"""
BARRIER_PLAY = StepPlay(1, PlaceBarrier(at=(0, 1)), MoveAction("N"), None)
BARRIER_EXPECT = [((0, 0), (5, 5))]
"""A turn spent building. Only the cop may, so which side holds it flips."""
CORNERED = (0, 6)
"""A cell from which ``THEIR_MOVES[0]`` would walk off the board."""
START = BoardState(
    grid_size=BOARD,
    cop=OUR_START if OUR_ROLE == "police" else THEIR_START,
    thief=THEIR_START if OUR_ROLE == "police" else OUR_START,
    barriers=frozenset(),
    step=0,
)
def board_with(theirs: tuple[int, int]) -> BoardState:
    return BoardState(
        grid_size=BOARD,
        cop=OUR_START if OUR_ROLE == "police" else theirs,
        thief=theirs if OUR_ROLE == "police" else OUR_START,
    )
def snapshot_at(cell: tuple[int, int]) -> dict[str, float]:
    trail = Trail()
    trail.deposit(emission(cell, BOARD))
    return trail.snapshot()
def honest(moves: list[str]) -> list[StepPlay]:
    plays = [
        StepPlay(step=n, ours=MoveAction("STAY"), theirs=MoveAction(m), disclosed=None)  # type: ignore[arg-type]
        for n, m in enumerate(moves, start=1)
    ]
    cells = [theirs for _, theirs in replay(START, AXES, OUR_ROLE, plays)]
    fields = trail_snapshots(cells, BOARD)
    return [
        StepPlay(step=play.step, ours=play.ours, theirs=play.theirs, disclosed=field)
        for play, field in zip(plays, fields, strict=True)
    ]
