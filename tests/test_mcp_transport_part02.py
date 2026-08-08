from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mcp_transport")).items() if not k.startswith("__")})

class TestItSatisfiesTheProtocol:
    def test_it_is_usable_as_a_transport(self) -> None:
        transport: Transport = FastMcpTransport()
        assert callable(transport.call)
    def test_the_real_client_drives_it(self, opponent: tuple[str, PeerInboxes]) -> None:
        url, _ = opponent
        client = OpponentClient(
            transport=FastMcpTransport(), settings=ClientSettings(opponent_url=url)
        )
        answer = client.call("receive_control", {"message": {"kind": "status", "sender": "thief"}})
        assert answer["ok"] is True
        assert client.sent, "the transport log recorded nothing about a real call"
