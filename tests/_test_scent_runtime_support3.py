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
def a_subgame(
    opponent: ScentedOpponent | None = None,
    moves: list[str] | None = None,
    max_steps: int = 3,
) -> tuple[SubGame, ScentedOpponent]:
    peer = opponent or ScentedOpponent()
    game = SubGame(
        role=OUR_ROLE,
        brain=ScriptedBrain(moves or [AWAY] * 4),  # type: ignore[arg-type]
        peer=peer,
        log=MatchLog(
            game_id="uoh26-s82kma9e",
            sub_game=1,
            role=OUR_ROLE,
            game_uid="u-0001",
            config_sha256="c" * 64,
        ),
        state=board(),
        axes=AXES,
        max_steps=max_steps,
        now=lambda: WHEN,
    )
    return game, peer

def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
