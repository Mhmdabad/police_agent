from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mcp_transport")).items() if not k.startswith("__")})

class TestARealCall:
    def test_it_reaches_the_opponents_inboxes(self, opponent: tuple[str, PeerInboxes]) -> None:
        url, _ = opponent
        answer = FastMcpTransport().call(
            url, "receive_control", {"message": {"kind": "status", "sender": "thief"}}, 10.0
        )
        assert answer["ok"] is True
    def test_the_message_actually_arrives(self, opponent: tuple[str, PeerInboxes]) -> None:
        url, inboxes = opponent
        FastMcpTransport().call(
            url, "receive_control", {"message": {"kind": "enable", "sender": "thief"}}, 10.0
        )
        assert not inboxes.controls.empty()
    def test_a_refusal_comes_back_as_a_value(self, opponent: tuple[str, PeerInboxes]) -> None:
        url, _ = opponent
        answer = FastMcpTransport().call(
            url, "receive_control", {"message": {"kind": "nonsense"}}, 10.0
        )
        assert answer["ok"] is False
    def test_submit_audit_uses_payload(self, opponent: tuple[str, PeerInboxes]) -> None:
        url, _ = opponent
        answer = FastMcpTransport().call(
            url, "submit_audit", {"payload": {"sender": "thief", "nonces": {}}}, 10.0
        )
        assert "ok" in answer
