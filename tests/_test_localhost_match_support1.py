from __future__ import annotations
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
def parameters() -> dict[str, Any]:
    body = json.loads((Path(__file__).resolve().parent.parent / "config/game.json").read_text())
    assert isinstance(body, dict)
    return body
def build_declaration(role: str, game_id: str, uid: str) -> MatchDeclaration:
    return declare(
        game_id=game_id,
        game_uid=uid,
        role=role,
        us=Team(
            name="uoh26-cops",
            members=("Mohammed Abad",),
            cop_repo=REPOS.cop_repo,
            thief_repo=REPOS.thief_repo,
        ),
        them=Team(
            name="uoh26-others",
            members=("Someone",),
            cop_repo=REPOS.opponent_cop_repo,
            thief_repo=REPOS.opponent_thief_repo,
        ),
        endpoints=Endpoints(ours="https://a.ngrok.io/mcp", theirs="https://b.ngrok.io/mcp"),
        hardware=Hardware(
            os_name="Linux",
            logical_cores=8,
            cpu_max_mhz=3600.0,
            ram_mb=16384,
            gpu=None,
            vram_mb=None,
            llm_model="claude-haiku-4-5",
        ),
        provenance=Provenance(
            code_version="1.0.0",
            group_name="uoh26-cops",
            sub_game=1,
            github_commit="a" * 40,
            dirty=False,
        ),
        llm_model="claude-haiku-4-5",
        token_ceiling=200_000,
        started_at="2026-08-05T11:00:00Z",
        key=None,
    )
def result_for(side: "Side", game_id: str, uid: str) -> Report:
    return Report(
        game_id=game_id,
        game_uid=uid,
        role=side.role,
        team="uoh26-cops",
        opponent_team="uoh26-others",
        repositories=REPOS,
        sub_games=(SubGameResult(sub_game=1, cop_score=0, thief_score=0, commit_hash="a" * 40),),
        total_tokens=0,
        agreed=True,
    )
def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])
def wait_for(port: int) -> None:
    deadline = time.monotonic() + 20.0
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    pytest.fail(f"nothing came up on {port}")  # pragma: no cover
class PlaysItsOwnPiece:
    def __init__(self, agent: str) -> None:
        self.agent = agent
    def decide(self, state: BoardState, **context: object) -> Decision:
        options = legal_moves(state, self.agent, AXES)  # type: ignore[arg-type]
        return Decision(action=MoveAction(move=options[0]), hint="", intent="truth")
def played_game(side: "Side") -> SubGame:
    game = side.runner.outcomes[0].game
    assert game is not None
    return game
def played_log(side: "Side") -> MatchLog:
    return side.runner.outcomes[0].log
@dataclass
class Side:
    role: str
    port: int
    inboxes: PeerInboxes
    log: MatchLog
    game: SubGame
    client: OpponentClient
    runner: MatchRunner

def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
