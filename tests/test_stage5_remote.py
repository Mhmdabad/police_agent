import json
from pathlib import Path
from typing import Any
import pytest
from cop_agent.domain.outcome import TechnicalLoss
from cop_agent.infra.handshake import ADDRESS_KEY, Greeting, Peering
from cop_agent.infra.inboxes import PeerInboxes
from cop_agent.infra.mcp_client import OPPONENT_URL_ENV, ClientSettings, OpponentClient
from cop_agent.runtime.orchestrator import PROTOCOL_VERSION, MatchAborted, Orchestrator
COP_URL = "https://cop-a1b2.ngrok-free.app/mcp"
THIEF_URL = "https://thief-c3d4.ngrok-free.app/mcp"
MOVED_THIEF_URL = "https://thief-e5f6.ngrok-free.app/mcp"
MOVED_COP_URL = "https://cop-9z8y.ngrok-free.app/mcp"
TURN = {
    "step": 1,
    "sender": "thief",
    "hint": "heading for the water",
    "smell_grid": {"3,3": 0.9},
    "commit": "a" * 64,
    "timestamp": "2026-08-04T09:00:00+00:00",
    "game_uid": "series-123",
    "sub_game": 1,
}
def unbind(payload: dict[str, Any]) -> Any:  # noqa: ANN401 - whatever the tool takes
    if len(payload) != 1:
        raise TypeError(f"a tool takes one argument; got {sorted(payload)}")
    return next(iter(payload.values()))
class Internet:
    def __init__(self) -> None:
        self.hosts: dict[str, Orchestrator] = {}
        self.delivered: list[tuple[str, str]] = []
    def listen(self, url: str, peer: Orchestrator) -> None:
        self.hosts[url] = peer
    def call(self, url: str, tool: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        del timeout
        if url not in self.hosts:
            raise ConnectionError(f"nothing answers at {url}")
        self.delivered.append((url, tool))
        return self.hosts[url].handle_inbound(tool, unbind(payload))
def peer(net: Internet, role: str, ours: str, theirs: str) -> Orchestrator:
    settings = ClientSettings.from_config({"opponent_url": theirs}, environ={})
    orchestrator = Orchestrator(
        PeerInboxes(game_uid="series-123", sub_game=1),
        OpponentClient(net, settings),
        role=role,
    )
    net.listen(ours, orchestrator)
    return orchestrator
@pytest.fixture
def wired() -> tuple[Internet, Orchestrator, Orchestrator]:
    net = Internet()
    cop = peer(net, "police", COP_URL, THIEF_URL)
    thief = peer(net, "thief", THIEF_URL, COP_URL)
    return net, cop, thief
