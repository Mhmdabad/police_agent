from __future__ import annotations
import json
from dataclasses import replace
from typing import Any, Protocol
import pytest
from cop_agent.domain.actions import MoveAction
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.domain.crypto import commit_of, nonce, step_record
from cop_agent.domain.memory import ScentMemory
from cop_agent.domain.scent import CENTRE_INTENSITY
from cop_agent.domain.trail import RETENTION
from cop_agent.infra.ceremony import (
    Acknowledgement,
    Commitment,
    FinalReveal,
    MatchCeremony,
    Reveal,
)
from cop_agent.infra.match_log import MatchLog
from cop_agent.runtime.subgame import SubGame
from cop_agent.strategy.base import Decision, StrategyContextError
from cop_agent.strategy.police_brain import PoliceBrain
WHEN = "2026-08-05T10:00:00+00:00"
AXES = AxisConvention()
GRID = 8
OUR_ROLE = "police"
THEIR_ROLE = "thief"
OUR_START = (0, 0)
THEIR_START = (6, 5)
AWAY = "S"
TWO_AWAY = (2, 0)
FORGED_FIELD = {"0,1": 0.9, "0,0": 0.62}
class Wireable(Protocol):
    def to_dict(self) -> dict[str, Any]: ...
def board() -> BoardState:
    return BoardState(
        grid_size=GRID,
        cop=OUR_START if OUR_ROLE == "police" else THEIR_START,
        thief=THEIR_START if OUR_ROLE == "police" else OUR_START,
        barriers=frozenset(),
        step=0,
    )
class ScriptedBrain:
    def __init__(self, moves: list[str]) -> None:
        self.moves = moves
        self.played = 0
    def decide(self, state: BoardState, **context: object) -> Decision:
        move = self.moves[min(self.played, len(self.moves) - 1)]
        self.played += 1
        return Decision(action=MoveAction(move=move), hint="somewhere", intent="truth")  # type: ignore[arg-type]
class RecordingBrain(ScriptedBrain):
    def __init__(self, moves: list[str]) -> None:
        super().__init__(moves)
        self.calls: list[tuple[BoardState, dict[str, object]]] = []
    def decide(self, state: BoardState, **context: object) -> Decision:
        self.calls.append((state, context))
        return super().decide(state, **context)

def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
