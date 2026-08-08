from typing import Any
import pytest
from cop_agent.infra.ceremony import CeremonyError, Commitment, FinalReveal, Reveal
from cop_agent.infra.inboxes import PeerInboxes
from cop_agent.infra.mcp_client import ClientSettings, OpponentClient
from cop_agent.infra.protocol import AuditPayload, TurnMessage
from cop_agent.runtime.peer import UNDECIDED, McpPeer, PeerTimeout
WHEN = "2026-08-05T11:00:00+00:00"
DIGEST = "a" * 64
OTHER = "b" * 64
class Recording:
    def __init__(self, answer: dict[str, Any] | None = None) -> None:
        self.answer = answer if answer is not None else {"ok": True}
        self.calls: list[tuple[str, dict[str, Any]]] = []
    def call(self, url: str, tool: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        self.calls.append((tool, payload))
        return self.answer
def a_peer(
    answer: dict[str, Any] | None = None, timeout: float = 0.05
) -> tuple[McpPeer, Recording, PeerInboxes]:
    transport = Recording(answer)
    inboxes = PeerInboxes()
    peer = McpPeer(
        role="police",
        client=OpponentClient(
            transport=transport,
            settings=ClientSettings(opponent_url="http://127.0.0.1:1/mcp"),
        ),
        inboxes=inboxes,
        now=WHEN,
        timeout=timeout,
        game_uid="series-123",
        sub_game=2,
    )
    return peer, transport, inboxes
def a_commitment(step: int = 1) -> Commitment:
    return Commitment(step=step, sender="police", commit=DIGEST, timestamp=WHEN)
