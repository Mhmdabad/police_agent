import asyncio
from typing import Any
import pytest
from fastmcp import Client
from cop_agent.infra.ceremony import Commitment
from cop_agent.infra.inboxes import PeerInboxes
from cop_agent.infra.mcp_client import ClientSettings, OpponentClient
from cop_agent.infra.mcp_server import build
from cop_agent.infra.protocol import AuditPayload
from cop_agent.runtime.orchestrator import Orchestrator
from cop_agent.runtime.peer import McpPeer
from cop_agent.shared.config import config_sha256
WHEN = "2026-08-05T12:00:00+00:00"
SETTINGS = ClientSettings(opponent_url="http://127.0.0.1:8802/mcp", retry_backoff_sec=0.0)
class Recorder:
    def __init__(self) -> None:
        self.sent: list[tuple[str, dict[str, Any]]] = []
    def call(self, url: str, tool: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        self.sent.append((tool, payload))
        return {"ok": True}
def outbound() -> list[tuple[str, dict[str, Any]]]:
    recorder = Recorder()
    client = OpponentClient(recorder, SETTINGS)
    orchestrator = Orchestrator(PeerInboxes(), client)
    parameters = {"board_and_agents": {"grid_size": 8}}
    orchestrator.announce(orchestrator.greeting("https://x.ngrok-free.app", "g1"))
    orchestrator.inboxes.negotiate({"config_sha256": config_sha256(parameters)})
    orchestrator.agree_config(parameters)
    peer = McpPeer(
        role="police",
        client=client,
        inboxes=PeerInboxes(),
        now=WHEN,
        game_uid="series-123",
        sub_game=1,
    )
    peer.send_commit(
        Commitment(
            step=1,
            sender="police",
            commit="a" * 64,
            timestamp=WHEN,
            game_uid="series-123",
            sub_game=1,
        )
    )
    peer._submit([], "in_progress")
    return recorder.sent
async def deliver(tool: str, payload: dict[str, Any]) -> dict[str, Any]:
    inboxes = PeerInboxes(game_uid="series-123", sub_game=1)
    async with Client(build(inboxes)) as client:
        answer = await client.call_tool(tool, payload)
    data = answer.data
    assert isinstance(data, dict), f"{tool} answered {type(data).__name__}, not an object"
    return data
class TestWhatWeSendIsWhatTheyAccept:
    def test_every_call_site_is_covered_here(self) -> None:
        assert {tool for tool, _ in outbound()} == {"negotiate", "receive_turn", "submit_audit"}
    @pytest.mark.parametrize(("tool", "payload"), outbound())
    def test_the_server_accepts_it(self, tool: str, payload: dict[str, Any]) -> None:
        assert asyncio.run(deliver(tool, payload))["ok"] is True, (
            f"{tool} refused {sorted(payload)}"
        )
    @pytest.mark.parametrize(("tool", "payload"), outbound())
    def test_it_carries_exactly_one_argument(self, tool: str, payload: dict[str, Any]) -> None:
        assert len(payload) == 1, f"{tool} sends {sorted(payload)}"
class TestTheDigestExchangeStillTravelsUnderMessage:
    def test_the_digest_is_nested_rather_than_spread(self) -> None:
        calls = [payload for tool, payload in outbound() if tool == "negotiate"]
        digest = [p for p in calls if "config_sha256" in str(p)][0]
        assert list(digest) == ["message"]
        assert "config_sha256" in digest["message"]
    def test_the_greeting_is_too(self) -> None:
        calls = [payload for tool, payload in outbound() if tool == "negotiate"]
        greeting = [p for p in calls if "public_url" in str(p)][0]
        assert list(greeting) == ["message"]
        assert greeting["message"]["greeting"]["role"] == "police"
class TestAuditPayloadShape:
    def test_submit_audit_sends_its_body_under_payload(self) -> None:
        sent = dict(outbound())["submit_audit"]
        assert list(sent) == ["payload"]
        assert AuditPayload.from_dict(sent["payload"]).sender == "police"
