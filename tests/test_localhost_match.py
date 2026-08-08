import json
import socket
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import pytest
from cop_agent.domain.actions import MoveAction
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.domain.lock import propose
from cop_agent.domain.rules import legal_moves
from cop_agent.infra.artefacts import ArtefactSet
from cop_agent.infra.config_file import lock
from cop_agent.infra.declaration import Endpoints, MatchDeclaration, Team
from cop_agent.infra.declaration import build as declare
from cop_agent.infra.inboxes import PeerInboxes
from cop_agent.infra.match_log import MatchLog
from cop_agent.infra.mcp_client import ClientSettings, OpponentClient
from cop_agent.infra.mcp_server import ServerSettings, build, serve
from cop_agent.infra.mcp_transport import FastMcpTransport
from cop_agent.infra.report import Report, Repositories, SubGameResult
from cop_agent.infra.step_zero import Hardware, Provenance
from cop_agent.runtime.match import MatchRunner, SubGameOutcome
from cop_agent.runtime.orchestrator import Orchestrator
from cop_agent.runtime.peer import McpPeer
from cop_agent.runtime.subgame import SubGame
from cop_agent.strategy.base import Decision
from cop_agent.ui.replay import load
from cop_agent.ui.verdict import Stamp, walk
REPOS = Repositories(
    cop_repo="https://github.com/Mhmdabad/police_agent",
    thief_repo="https://github.com/Mhmdabad/theif_agent",
    opponent_cop_repo="https://github.com/other/police",
    opponent_thief_repo="https://github.com/other/thief",
)
WHEN = "2026-08-05T11:00:00+00:00"
AXES = AxisConvention()
STEPS = 3

from importlib import import_module as _import_module
_supports = ['_test_localhost_match_support1', '_test_localhost_match_support2']
_loaded = [_import_module(_name) for _name in _supports]
for _module in _loaded:
    globals().update({k: v for k, v in vars(_module).items() if not k.startswith("__") and k != "_install"})
for _module in _loaded:
    _module._install(globals())
