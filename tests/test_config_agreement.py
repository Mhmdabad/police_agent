import queue
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import pytest
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.domain.outcome import TechnicalLoss
from cop_agent.infra.inboxes import PeerInboxes
from cop_agent.infra.mcp_client import ClientSettings, OpponentClient
from cop_agent.infra.mcp_server import ServerSettings, build, serve
from cop_agent.infra.mcp_transport import FastMcpTransport
from cop_agent.infra.protocol import TurnMessage
from cop_agent.runtime.match import MatchRunner
from cop_agent.runtime.orchestrator import MatchAborted, Orchestrator
from cop_agent.shared.config import config_sha256, digests_agree
from test_localhost_match import (  # noqa: E402
    WHEN,
    PlaysItsOwnPiece,
    build_declaration,
    free_port,
    parameters,
    wait_for,
)
from test_match import a_peering  # noqa: E402
GAME_UID = "u-0001"
"""The series these tests negotiate. Matches the declaration they build."""
OTHER_UID = "u-0002"
"""A different series. A digest bound to it is not an answer about this one."""
GAME_ID = "uoh26-s82kma9e"
OUR_ROLE = "police"
"""The role this repository plays. The sibling names the other one."""
THEIR_ROLE = "thief"
PATIENCE = 20.0
"""Long enough for two local sockets, short enough that a hang is a failure."""
BRIEF = 1.5
"""The window used when the point of the test is that nothing ever arrives."""
def altered() -> dict[str, Any]:
    config = parameters()
    config["world"]["map_area"] = "London"
    return config
def agreed_digest() -> str:
    return config_sha256(parameters())
@dataclass
class Side:
    role: str
    inboxes: PeerInboxes
    orchestrator: Orchestrator
    def clear(self) -> None:
        self.inboxes.agreements = queue.Queue[dict[str, Any]]()
        self.inboxes.digests = queue.Queue[dict[str, Any]]()
        self.inboxes.scent_locks = queue.Queue[dict[str, Any]]()
        self.inboxes.turns = queue.Queue[TurnMessage]()
        self.inboxes.accepted_turns.clear()
        self.inboxes.rejected.clear()
    def send(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.orchestrator.call_opponent("negotiate", {"message": body})
def a_side(role: str, opponent_port: int) -> Side:
    inboxes = PeerInboxes()
    client = OpponentClient(
        transport=FastMcpTransport(),
        settings=ClientSettings(
            opponent_url=f"http://127.0.0.1:{opponent_port}/mcp",
            response_timeout_sec=10.0,
            max_retries=1,
            retry_backoff_sec=0.5,
        ),
    )
    return Side(
        role=role,
        inboxes=inboxes,
        orchestrator=Orchestrator(inboxes=inboxes, client=client, role=role),
    )
@pytest.fixture(scope="module")
def wire() -> Iterator[tuple[Side, Side]]:
    our_port, their_port = free_port(), free_port()
    ours, theirs = a_side(OUR_ROLE, their_port), a_side(THEIR_ROLE, our_port)
    for side, port in ((ours, our_port), (theirs, their_port)):
        host = build(side.inboxes, name=f"{side.role}-config-gate")
        threading.Thread(
            target=serve,
            args=(host, ServerSettings(port=port, host="127.0.0.1")),
            daemon=True,
        ).start()
        wait_for(port)
    yield ours, theirs
def fresh(wire: tuple[Side, Side]) -> tuple[Side, Side]:
    for side in wire:
        side.clear()
    return wire
def concurrently(work: dict[str, Callable[[], Any]], patience: float = 60.0) -> dict[str, Any]:
    done: dict[str, Any] = {}
    def run(name: str, call: Callable[[], Any]) -> None:
        try:
            done[name] = call()
        except BaseException as exc:  # noqa: BLE001 - reported below, not swallowed
            done[name] = exc
    threads = [threading.Thread(target=run, args=(n, c)) for n, c in work.items()]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=patience)
    assert not [t for t in threads if t.is_alive()], (
        "a side never returned; the two peers deadlocked waiting for each other"
    )
    return done
def gate(side: Side, config: dict[str, Any], timeout: float = PATIENCE) -> Callable[[], str]:
    return lambda: side.orchestrator.agree_config(config, game_uid=GAME_UID, timeout=timeout)
def both_run(
    wire: tuple[Side, Side],
    our_config: dict[str, Any],
    their_config: dict[str, Any],
    timeout: float = PATIENCE,
) -> dict[str, Any]:
    ours, theirs = fresh(wire)
    return concurrently(
        {"ours": gate(ours, our_config, timeout), "theirs": gate(theirs, their_config, timeout)}
    )
def a_runner(side: Side, config: dict[str, Any], directory: Path) -> MatchRunner:
    return MatchRunner(
        orchestrator=side.orchestrator,
        declaration=build_declaration(side.role, GAME_ID, GAME_UID),
        parameters=config,
        brain=PlaysItsOwnPiece("cop" if side.role == "police" else "thief"),  # type: ignore[arg-type]
        axes=AxisConvention(),
        start=BoardState(grid_size=8, cop=(0, 0), thief=(6, 5), barriers=frozenset(), step=0),
        max_steps=3,
        directory=directory,
        now=lambda: WHEN,
        peering=a_peering(side.role),
    )
