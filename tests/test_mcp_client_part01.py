from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mcp_client")).items() if not k.startswith("__")})

class TestHappyPath:
    def test_returns_the_response(self) -> None:
        client = OpponentClient(FakeTransport({"accepted": True}), SETTINGS)
        assert client.call("receive_move", {"move": "N"}) == {"accepted": True}
    def test_sends_to_the_configured_url_with_the_deadline(self) -> None:
        transport = FakeTransport({"ok": True})
        OpponentClient(transport, SETTINGS).call("ping", {})
        assert transport.calls[0]["url"] == "http://127.0.0.1:8802/mcp"
        assert transport.calls[0]["timeout"] == 30.0
    def test_succeeds_on_the_first_attempt(self) -> None:
        client = OpponentClient(FakeTransport({"ok": True}), SETTINGS)
        client.call("ping", {})
        assert client.attempts == 1
