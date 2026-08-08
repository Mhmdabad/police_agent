from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mcp_transport")).items() if not k.startswith("__")})

class TestTheHttpClientsOwnFailures:
    class Failing:
        error: BaseException = RuntimeError("replaced per test")
        def __init__(self, url: str) -> None:
            self.url = url
        async def __aenter__(self) -> "TestTheHttpClientsOwnFailures.Failing":
            raise type(self).error
        async def __aexit__(self, *exc: object) -> None:
            return None
    def raising(self, error: BaseException, monkeypatch: pytest.MonkeyPatch) -> None:
        client = type("C", (self.Failing,), {"error": error})
        monkeypatch.setattr("cop_agent.infra.mcp_transport.Client", client)
    def test_a_connect_error_becomes_the_vocabulary_the_retry_budget_knows(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import httpx
        self.raising(httpx.ConnectError(""), monkeypatch)
        with pytest.raises(ConnectionError, match="could not reach"):
            FastMcpTransport().call("https://x.ngrok-free.app/mcp", "receive_turn", {}, 1.0)
    def test_it_names_the_two_things_that_are_actually_wrong(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import httpx
        self.raising(httpx.ConnectError(""), monkeypatch)
        with pytest.raises(ConnectionError) as raised:
            FastMcpTransport().call("https://x.ngrok-free.app/mcp", "receive_turn", {}, 1.0)
        assert "tunnel" in str(raised.value)
        assert "agent has" in str(raised.value)
    def test_our_own_bugs_are_not_disguised_as_unreachable_opponents(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self.raising(KeyError("a bug of ours"), monkeypatch)
        with pytest.raises(KeyError):
            FastMcpTransport().call("https://x.ngrok-free.app/mcp", "receive_turn", {}, 1.0)
