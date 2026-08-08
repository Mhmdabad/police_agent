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
"""A move legal from :data:`OUR_START` four times over, in a straight line."""
TWO_AWAY = (2, 0)
"""Where two :data:`AWAY` moves put us."""
FORGED_FIELD = {"0,1": 0.9, "0,0": 0.62}
"""Well formed, correctly rounded, on the board — and not what was emitted."""

from importlib import import_module as _import_module
_supports = ['_test_scent_runtime_support1', '_test_scent_runtime_support2', '_test_scent_runtime_support3']
_loaded = [_import_module(_name) for _name in _supports]
for _module in _loaded:
    globals().update({k: v for k, v in vars(_module).items() if not k.startswith("__") and k != "_install"})
for _module in _loaded:
    _module._install(globals())
