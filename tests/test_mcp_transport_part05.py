from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mcp_transport")).items() if not k.startswith("__")})

class TestATunnelAnsweringForADeadPeer:
    class Answering:
        status = 502
        def __init__(self, url: str) -> None:
            self.url = url
        async def __aenter__(self) -> "TestATunnelAnsweringForADeadPeer.Answering":
            raise self.error(type(self).status)
        async def __aexit__(self, *exc: object) -> None:
            return None
        @staticmethod
        def error(status: int) -> Exception:
            class Response:
                status_code = status
            class HTTPStatusError(Exception):
                response = Response()
            return HTTPStatusError(
                f"Server error '{status}' for url 'https://x.ngrok-free.app/mcp'"
            )
    def transport_raising(self, status: int, monkeypatch: pytest.MonkeyPatch) -> None:
        client = type("C", (self.Answering,), {"status": status})
        monkeypatch.setattr("cop_agent.infra.mcp_transport.Client", client)
    @pytest.mark.parametrize("status", sorted(UPSTREAM_DEAD))
    def test_a_gateway_reporting_a_dead_peer_is_an_unreachable_peer(
        self, status: int, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self.transport_raising(status, monkeypatch)
        with pytest.raises(ConnectionError, match=str(status)):
            FastMcpTransport().call("https://x.ngrok-free.app/mcp", "negotiate", {}, 1.0)
    def test_it_says_what_to_check_rather_than_quoting_the_proxy(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self.transport_raising(502, monkeypatch)
        with pytest.raises(ConnectionError) as raised:
            FastMcpTransport().call("https://x.ngrok-free.app/mcp", "negotiate", {}, 1.0)
        assert "nothing is listening behind it" in str(raised.value)
        assert "different port" in str(raised.value)
    def test_a_peer_that_answered_is_not_an_unreachable_peer(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self.transport_raising(404, monkeypatch)
        with pytest.raises(Exception) as raised:
            FastMcpTransport().call("https://x.ngrok-free.app/mcp", "negotiate", {}, 1.0)
        assert not isinstance(raised.value, ConnectionError)
    def test_an_exception_carrying_no_status_is_left_alone(self) -> None:
        assert upstream_status(ValueError("nothing http about this")) is None
    def test_a_non_numeric_status_is_not_trusted(self) -> None:
        class Odd(Exception):
            response = type("R", (), {"status_code": "502"})()
        assert upstream_status(Odd()) is None
