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
def a_side(role: str, port: int, opponent_port: int) -> Side:
    inboxes = PeerInboxes(game_uid="u-0001", sub_game=1)
    log = MatchLog(
        game_id="uoh26-s82kma9e",
        sub_game=1,
        role=role,
        game_uid="u-0001",
        config_sha256="c" * 64,
    )
    client = OpponentClient(
        transport=FastMcpTransport(),
        settings=ClientSettings(
            opponent_url=f"http://127.0.0.1:{opponent_port}/mcp",
            response_timeout_sec=20.0,
            max_retries=3,
            retry_backoff_sec=5.0,
        ),
    )
    game = SubGame(
        role=role,
        brain=PlaysItsOwnPiece("cop" if role == "police" else "thief"),  # type: ignore[arg-type]
        peer=McpPeer(
            role=role,
            client=client,
            inboxes=inboxes,
            game_uid="u-0001",
            sub_game=1,
            now=WHEN,
            timeout=25.0,
        ),
        log=log,
        state=BoardState(grid_size=8, cop=(0, 0), thief=(6, 5), barriers=frozenset(), step=0),
        axes=AXES,
        max_steps=STEPS,
        now=lambda: WHEN,
    )
    runner = MatchRunner(
        orchestrator=Orchestrator(inboxes=inboxes, client=client, role=role),
        declaration=build_declaration(role, "uoh26-s82kma9e", "u-0001"),
        parameters=parameters(),
        brain=PlaysItsOwnPiece("cop" if role == "police" else "thief"),  # type: ignore[arg-type]
        axes=AXES,
        start=BoardState(grid_size=8, cop=(0, 0), thief=(6, 5), barriers=frozenset(), step=0),
        max_steps=STEPS,
        directory=Path("/tmp") / f"unused-{role}",
        now=lambda: WHEN,
    )
    return Side(
        role=role, port=port, inboxes=inboxes, log=log, game=game, client=client, runner=runner
    )
@pytest.fixture(scope="module")
def played(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[Side, Side, Path]]:
    cop_port, thief_port = free_port(), free_port()
    cop = a_side("police", cop_port, thief_port)
    thief = a_side("thief", thief_port, cop_port)
    for side in (cop, thief):
        host = build(side.inboxes, name=f"{side.role}-under-test")
        threading.Thread(
            target=serve,
            args=(host, ServerSettings(port=side.port, host="127.0.0.1")),
            daemon=True,
        ).start()
    wait_for(cop_port)
    wait_for(thief_port)
    failures: dict[str, BaseException] = {}
    def run(side: Side) -> None:
        try:
            side.runner.agree(timeout=25.0)
            side.runner.play_sub_game(1, timeout=25.0)
        except BaseException as exc:  # noqa: BLE001 - reported below, not swallowed
            failures[side.role] = exc
    threads = [threading.Thread(target=run, args=(side,)) for side in (cop, thief)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=120.0)
    if failures:
        pytest.fail("; ".join(f"{role}: {exc!r}" for role, exc in failures.items()))
    for thread in threads:
        assert not thread.is_alive(), "a side never finished; the match deadlocked"
    yield cop, thief, tmp_path_factory.mktemp("artefacts")

def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
