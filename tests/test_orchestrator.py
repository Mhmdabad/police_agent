import contextlib
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any
import pytest
from cop_agent.domain.outcome import TechnicalLoss
from cop_agent.infra.handshake import Peering
from cop_agent.infra.inboxes import PeerInboxes
from cop_agent.infra.mcp_client import ClientSettings, OpponentClient
from cop_agent.runtime.orchestrator import PROTOCOL_VERSION, MatchAborted, Orchestrator
from cop_agent.shared.config import config_sha256
SETTINGS = ClientSettings(opponent_url="http://127.0.0.1:8802/mcp", retry_backoff_sec=0.0)
OUR_URL = "https://cop-a1b2.ngrok-free.app"
THEIR_URL = "https://thief-c3d4.ngrok-free.app"
TURN = {
    "step": 1,
    "sender": "thief",
    "hint": "slipping away",
    "smell_grid": {"3,3": 0.9},
    "commit": "a" * 64,
    "timestamp": "2026-08-03T09:00:00+00:00",
    "game_uid": "series-123",
    "sub_game": 1,
}
def shipped() -> dict[str, Any]:
    text = (Path(__file__).parents[1] / "config/game.json").read_text()
    loaded: dict[str, Any] = json.loads(text)
    return loaded
class FakeTransport:
    def __init__(self, *outcomes: object) -> None:
        self._outcomes = list(outcomes)
        self.calls: list[dict[str, Any]] = []
    def call(self, url: str, tool: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        self.calls.append({"tool": tool, "payload": payload})
        outcome = self._outcomes.pop(0) if self._outcomes else {"ok": True}
        if isinstance(outcome, Exception):
            raise outcome
        assert isinstance(outcome, dict)
        return outcome
def orchestrator(*outcomes: object) -> tuple[Orchestrator, FakeTransport]:
    transport = FakeTransport(*outcomes)
    return (
        Orchestrator(
            PeerInboxes(game_uid="series-123", sub_game=1),
            OpponentClient(transport, SETTINGS),
        ),
        transport,
    )
def inbound(
    orch: Orchestrator,
    role: str = "thief",
    url: str = THEIR_URL,
    version: str = PROTOCOL_VERSION,
) -> None:
    orch.inboxes.negotiate(
        {
            "greeting": {
                "role": role,
                "group_id": "them",
                "public_url": url,
                "protocol_version": version,
            }
        }
    )
ROTATED = "https://thief-e5f6.ngrok-free.app"
def answered(orch: Orchestrator, digest: str, game_uid: str = "") -> None:
    body: dict[str, Any] = {"config_sha256": digest}
    if game_uid:
        body["game_uid"] = game_uid
    orch.inboxes.negotiate(body)
