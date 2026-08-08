from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mcp_transport")).items() if not k.startswith("__")})

class TestFailuresTravelUpUntranslated:
    def test_an_unreachable_port_raises_rather_than_returning(self) -> None:
        with pytest.raises(Exception, match=r".+"):
            FastMcpTransport().call(
                f"http://127.0.0.1:{free_port()}/mcp", "receive_control", {"message": {}}, 2.0
            )
    def test_the_retry_budget_converts_it_into_unreachable(self) -> None:
        client = OpponentClient(
            transport=FastMcpTransport(),
            settings=ClientSettings(
                opponent_url=f"http://127.0.0.1:{free_port()}/mcp",
                response_timeout_sec=2.0,
                max_retries=1,
                retry_backoff_sec=0.0,
            ),
        )
        with pytest.raises(OpponentUnreachableError):
            client.call("receive_control", {"message": {}})
