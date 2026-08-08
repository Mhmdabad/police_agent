import json
import socket
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
import pytest
from cop_agent.domain.actions import MoveAction
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState, Move
from cop_agent.domain.scent_audit import trail_snapshots
from cop_agent.infra.ceremony import Commitment
from cop_agent.infra.inboxes import PeerInboxes
from cop_agent.infra.match_log import MatchLog
from cop_agent.infra.mcp_client import ClientSettings, OpponentClient
from cop_agent.infra.mcp_server import ServerSettings, build, serve
from cop_agent.infra.mcp_transport import FastMcpTransport
from cop_agent.runtime.peer import McpPeer
from cop_agent.runtime.subgame import SubGame
from cop_agent.strategy.base import Decision
WHEN = "2026-08-05T11:00:00+00:00"
AXES = AxisConvention()
STEPS = 3
GRID = 8
COP_START = (0, 0)
THIEF_START = (6, 5)
SCRIPT: dict[str, list[Move]] = {"police": ["S", "S", "S"], "thief": ["N", "N", "N"]}
"""Both sides march, so the trail is a moving hill rather than a fixed blob.
A stationary emitter would pass every assertion below while proving nothing
about whether decay ran, since a re-emitted centre is 0.9 either way.
"""
def start_board() -> BoardState:
    return BoardState(
        grid_size=GRID, cop=COP_START, thief=THIEF_START, barriers=frozenset(), step=0
    )
def cells_walked(start: tuple[int, int], moves: list[Move]) -> list[tuple[int, int]]:
    delta = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1), "STAY": (0, 0)}
    here, walked = start, []
    for move in moves:
        drow, dcol = delta[move]
        here = (here[0] + drow, here[1] + dcol)
        walked.append(here)
    return walked
class Marches:
    def __init__(self, moves: list[Move]) -> None:
        self.moves = moves
        self.played = 0
    def decide(self, state: BoardState, **context: object) -> Decision:
        move = self.moves[min(self.played, len(self.moves) - 1)]
        self.played += 1
        return Decision(action=MoveAction(move=move), hint="over there", intent="truth")
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
@dataclass
class Side:
    role: str
    port: int
    inboxes: PeerInboxes
    game: SubGame
    @property
    def sent(self) -> list[dict[str, float] | None]:
        return [self.game.ceremony.at(step).revealed_ours.scent for step in range(1, STEPS + 1)]  # type: ignore[union-attr]
    @property
    def received(self) -> list[dict[str, float] | None]:
        return [self.game.ceremony.at(step).revealed_theirs.scent for step in range(1, STEPS + 1)]  # type: ignore[union-attr]
def a_side(role: str, port: int, opponent_port: int) -> Side:
    inboxes = PeerInboxes(game_uid="u-0001", sub_game=1)
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
        brain=Marches(SCRIPT[role]),  # type: ignore[arg-type]
        peer=McpPeer(
            role=role,
            client=client,
            inboxes=inboxes,
            game_uid="u-0001",
            sub_game=1,
            now=WHEN,
            timeout=25.0,
        ),
        log=MatchLog(
            game_id="uoh26-s82kma9e",
            sub_game=1,
            role=role,
            game_uid="u-0001",
            config_sha256="c" * 64,
        ),
        state=start_board(),
        axes=AXES,
        max_steps=STEPS,
        now=lambda: WHEN,
    )
    return Side(role=role, port=port, inboxes=inboxes, game=game)
@pytest.fixture(scope="module")
def played() -> Iterator[tuple[Side, Side]]:
    cop_port, thief_port = free_port(), free_port()
    cop, thief = a_side("police", cop_port, thief_port), a_side("thief", thief_port, cop_port)
    for side in (cop, thief):
        host = build(side.inboxes, name=f"{side.role}-scent-under-test")
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
            side.game.play()
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
    yield cop, thief
def _moves() -> list[Move]:
    return ["N", "S", "E", "W", "STAY"]
