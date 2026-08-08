from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mcp_transport")).items() if not k.startswith("__")})

class TestANonMappingResultIsAProtocolViolation:
    def test_it_is_named_rather_than_coerced(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class Answer:
            data = "not a mapping"
        class FakeClient:
            def __init__(self, url: str) -> None:
                self.url = url
            async def __aenter__(self) -> "FakeClient":
                return self
            async def __aexit__(self, *exc: object) -> None:
                return None
            async def call_tool(self, name: str, arguments: object, timeout: float) -> Answer:
                return Answer()
        monkeypatch.setattr("cop_agent.infra.mcp_transport.Client", FakeClient)
        with pytest.raises(TypeError, match="is not speaking it"):
            FastMcpTransport().call("http://x/mcp", "receive_control", {}, 1.0)
    def test_an_already_correct_exception_is_not_re_wrapped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class Refusing:
            def __init__(self, url: str) -> None:
                self.url = url
            async def __aenter__(self) -> "Refusing":
                raise OSError("no route to host")
            async def __aexit__(self, *exc: object) -> None:
                return None
        monkeypatch.setattr("cop_agent.infra.mcp_transport.Client", Refusing)
        with pytest.raises(OSError, match="no route to host") as raised:
            FastMcpTransport().call("http://x/mcp", "receive_control", {}, 1.0)
        assert type(raised.value) is OSError, "an OSError became something else"
