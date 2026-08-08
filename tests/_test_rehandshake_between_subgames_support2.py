from __future__ import annotations
import json
import socket
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import pytest
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.domain.outcome import TechnicalLoss
from cop_agent.infra.ceremony import Commitment
from cop_agent.infra.handshake import Peering
from cop_agent.infra.inboxes import (
    ACK,
    DIGEST_KEY,
    SCENT_DIGEST_KEY,
    SCENT_KEY,
    SERIES_KEY,
    PeerInboxes,
)
from cop_agent.infra.match_log import MatchLog
from cop_agent.infra.mcp_client import ClientSettings, OpponentClient
from cop_agent.infra.mcp_server import ServerSettings, build, serve
from cop_agent.infra.mcp_transport import FastMcpTransport
from cop_agent.runtime.match import MatchRunner, SubGameOutcome
from cop_agent.runtime.orchestrator import (
    GREETING_TIMEOUT_SEC,
    PROTOCOL_VERSION,
    MatchAborted,
    Orchestrator,
)
from cop_agent.runtime.peer import McpPeer
from cop_agent.shared.appendix_f import book_int
from cop_agent.shared.config import config_sha256
from cop_agent.strategy.police_brain import PoliceBrain
from cop_agent.ui.replay import load
from cop_agent.ui.verdict import Stamp, walk
from test_localhost_match import (
    PlaysItsOwnPiece,
    build_declaration,
    free_port,
    parameters,
    wait_for,
)
from test_match import an_outcome
ROLE = "police"
OPPONENT = "thief"
GROUP = "s82kma9e"
GAME_ID = "uoh26-s82kma9e"
GAME_UID = "u-0001"
WHEN = "2026-08-05T12:00:00+00:00"
AXES = AxisConvention()
COMMIT = "a" * 64
BOOK_SERIES = book_int("network_and_league", "num_games")
BOOK_RETRIES = book_int("rate_limiter_gatekeeper", "max_retries")
BOOK_RESPONSE_TIMEOUT = book_int("network_and_league", "response_timeout_sec")
BOUNDARIES = [2, 3, 4, 5, 6]
OUR_URL = "https://cop-a1b2.ngrok-free.app"
THEIR_URL = "https://thief-c3d4.ngrok-free.app"
ROTATED = "https://thief-e5f6.ngrok-free.app"
PRIVATE = "http://10.0.0.7:8802"
LOOPBACK = "http://127.0.0.1:8802"
AT_THEIRS = f"{THEIR_URL}/mcp"
AT_ROTATED = f"{ROTATED}/mcp"
Install = Callable[..., None]
STEPS = 2
def plays(after: Callable[[int], None] = lambda _: None) -> Callable[..., SubGameOutcome]:
    def play(self: MatchRunner, number: int, timeout: float = 30.0) -> SubGameOutcome:
        McpPeer(
            role=self.role,
            client=self.orchestrator.client,
            inboxes=self.orchestrator.inboxes,
            game_uid=self.declaration.game_uid,
            sub_game=number,
            now=WHEN,
            timeout=timeout,
        ).send_commit(Commitment(step=1, sender=self.role, commit=COMMIT, timestamp=WHEN))
        outcome = an_outcome(number)
        self.outcomes.append(outcome)
        after(number)
        return outcome
    return play
@pytest.fixture
def stub(monkeypatch: pytest.MonkeyPatch) -> Callable[[Callable[[int], None]], None]:
    def install(after: Callable[[int], None] = lambda _: None) -> None:
        monkeypatch.setattr(MatchRunner, "play_sub_game", plays(after))
    return install
@dataclass
class Live:
    role: str
    port: int
    inboxes: PeerInboxes
    runner: MatchRunner
    transport: FastMcpTransport
def a_live_side(role: str, port: int, opponent_port: int, where: Path) -> Live:
    inboxes = PeerInboxes()
    transport = FastMcpTransport()
    client = OpponentClient(
        transport=transport,
        settings=ClientSettings(
            opponent_url=f"http://127.0.0.1:{opponent_port}/mcp",
            response_timeout_sec=20.0,
            retry_backoff_sec=1.0,
        ),
    )
    runner = MatchRunner(
        orchestrator=Orchestrator(inboxes=inboxes, client=client, role=role),
        declaration=build_declaration(role, GAME_ID, GAME_UID),
        parameters=parameters(),
        brain=PlaysItsOwnPiece("cop" if role == "police" else "thief"),  # type: ignore[arg-type]
        axes=AXES,
        start=BoardState(grid_size=8, cop=(0, 0), thief=(6, 5), barriers=frozenset(), step=0),
        max_steps=STEPS,
        directory=where / role,
        now=lambda: WHEN,
    )
    return Live(role=role, port=port, inboxes=inboxes, runner=runner, transport=transport)

def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
