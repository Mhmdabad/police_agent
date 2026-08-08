from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mcp_transport")).items() if not k.startswith("__")})

class TestOneSessionForTheWholeMatch:
    def test_a_second_call_reuses_the_first_session(
        self, opponent: tuple[str, PeerInboxes]
    ) -> None:
        live, _ = opponent
        transport = FastMcpTransport()
        try:
            transport.call(
                live, "receive_control", {"message": {"kind": "status", "sender": "thief"}}, 5.0
            )
            first = transport._client
            transport.call(
                live, "receive_control", {"message": {"kind": "status", "sender": "thief"}}, 5.0
            )
            assert transport._client is first, "reconnected when it did not need to"
        finally:
            transport.close()
    def test_a_new_address_reconnects(self, opponent: tuple[str, PeerInboxes]) -> None:
        live, _ = opponent
        transport = FastMcpTransport()
        try:
            transport.call(
                live, "receive_control", {"message": {"kind": "status", "sender": "thief"}}, 5.0
            )
            first = transport._client
            transport._connected_to = "http://127.0.0.1:1/mcp"  # pretend we moved
            transport.call(
                live, "receive_control", {"message": {"kind": "status", "sender": "thief"}}, 5.0
            )
            assert transport._client is not first
        finally:
            transport.close()
    def test_a_failed_call_does_not_leave_a_broken_session_behind(
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
        transport = FastMcpTransport()
        try:
            with pytest.raises(OSError, match="no route to host"):
                transport.call("http://127.0.0.1:1/mcp", "receive_turn", {}, 1.0)
            assert transport._client is None, "kept a session that had already failed"
        finally:
            transport.close()
    def test_closing_twice_is_harmless(self, opponent: tuple[str, PeerInboxes]) -> None:
        live, _ = opponent
        transport = FastMcpTransport()
        transport.call(
            live, "receive_control", {"message": {"kind": "status", "sender": "thief"}}, 5.0
        )
        transport.close()
        transport.close()
    def test_closing_without_ever_calling_is_harmless(self) -> None:
        FastMcpTransport().close()
    def test_a_close_that_fails_does_not_replace_the_real_error(self) -> None:
        class Hostile:
            async def __aexit__(self, *exc: object) -> None:
                raise RuntimeError("the close itself failed")
        transport = FastMcpTransport()
        transport._running_loop()
        transport._client = Hostile()
        transport.drop()
        assert transport._client is None
        transport.close()
