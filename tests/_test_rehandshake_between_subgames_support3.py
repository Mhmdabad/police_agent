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
@pytest.fixture(scope="module")
def series(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[Live, Live]]:
    where = tmp_path_factory.mktemp("series")
    our_port, their_port = free_port(), free_port()
    us = a_live_side(ROLE, our_port, their_port, where)
    them = a_live_side(OPPONENT, their_port, our_port, where)
    for side in (us, them):
        host = build(side.inboxes, name=f"{side.role}-series")
        threading.Thread(
            target=serve,
            args=(host, ServerSettings(port=side.port, host="127.0.0.1")),
            daemon=True,
        ).start()
    wait_for(our_port)
    wait_for(their_port)
    failures: dict[str, BaseException] = {}
    def run(side: Live) -> None:
        try:
            ours = side.runner.orchestrator.greeting(f"http://127.0.0.1:{side.port}/mcp", GROUP)
            side.runner.peering = side.runner.orchestrator.open_series(
                ours, side.runner.directory, GAME_ID, timeout=25.0
            )
            side.runner.agree(timeout=25.0)
            side.runner.play_series(timeout=25.0)
        except BaseException as exc:  # noqa: BLE001 - reported below, not swallowed
            failures[side.role] = exc
    threads = [threading.Thread(target=run, args=(side,)) for side in (us, them)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=300.0)
    for thread in threads:
        assert not thread.is_alive(), "a side never finished; the series deadlocked"
    if failures:
        pytest.fail("; ".join(f"{role}: {exc!r}" for role, exc in failures.items()))
    yield us, them
    for side in (us, them):
        side.transport.close()

def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
