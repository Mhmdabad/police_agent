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
def greets(url: str, **changed: str) -> dict[str, Any]:
    return {
        "greeting": {
            "role": OPPONENT,
            "group_id": "them",
            "public_url": url,
            "protocol_version": PROTOCOL_VERSION,
            **changed,
        }
    }
@dataclass
class ScriptedPeer:
    inboxes: PeerInboxes
    announce: dict[str, Any] | None = field(default_factory=lambda: greets(THEIR_URL))
    failing: frozenset[int] = frozenset()
    """Which ``negotiate`` attempts, counted from one, fail as a dead tunnel."""
    calls: list[tuple[str, str]] = field(default_factory=list, init=False)
    negotiations: int = field(default=0, init=False)
    def call(self, url: str, tool: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        self.calls.append((url, tool))
        if tool != "negotiate":
            return dict(ACK)
        self.negotiations += 1
        if self.announce is not None:
            self.inboxes.negotiate(dict(self.announce))
        if self.negotiations in self.failing:
            raise ConnectionError("the address this call named is a tunnel that no longer exists")
        return dict(ACK)
    @property
    def tools(self) -> list[str]:
        return [tool for _, tool in self.calls]
    def where(self, tool: str) -> list[str]:
        return [url for url, called in self.calls if called == tool]
def a_runner(tmp_path: Path, transport: ScriptedPeer, peering: Peering | None) -> MatchRunner:
    return MatchRunner(
        orchestrator=Orchestrator(
            inboxes=transport.inboxes,
            client=OpponentClient(
                transport=transport,
                settings=ClientSettings(opponent_url=THEIR_URL, retry_backoff_sec=0.0),
            ),
            role=ROLE,
        ),
        declaration=build_declaration(ROLE, GAME_ID, GAME_UID),
        parameters=parameters(),
        brain=PoliceBrain(),
        axes=AXES,
        start=BoardState(grid_size=8, cop=(0, 0), thief=(6, 5), barriers=frozenset(), step=0),
        max_steps=2,
        directory=tmp_path,
        now=lambda: WHEN,
        peering=peering,
    )
def opened(tmp_path: Path, transport: ScriptedPeer) -> MatchRunner:
    orchestrator = Orchestrator(
        inboxes=transport.inboxes,
        client=OpponentClient(
            transport=transport,
            settings=ClientSettings(opponent_url=THEIR_URL, retry_backoff_sec=0.0),
        ),
        role=ROLE,
    )
    peering = orchestrator.open_series(orchestrator.greeting(OUR_URL, GROUP), tmp_path, GAME_ID)
    runner = a_runner(tmp_path, transport, peering)
    runner.orchestrator = orchestrator
    return runner

def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
