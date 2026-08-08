from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tunnel")).items() if not k.startswith("__")})

class TestDiscovery:
    def test_an_explicit_variable_wins_over_discovery(self) -> None:
        endpoint = discover({PUBLIC_URL_ENV: PUBLIC}, ngrok_reader=lambda: ngrok_body("https://o"))
        assert endpoint is not None
        assert endpoint.host == "a1b2c3d4.ngrok-free.app"
    def test_a_bad_explicit_variable_raises_rather_than_falling_back(self) -> None:
        with pytest.raises(NotPublicError):
            discover({PUBLIC_URL_ENV: "http://localhost:8801/mcp"}, ngrok_reader=lambda: "")
    def test_it_falls_back_to_the_ngrok_agent(self) -> None:
        endpoint = discover({}, ngrok_reader=lambda: ngrok_body(PUBLIC))
        assert endpoint is not None and endpoint.url == f"{PUBLIC}{MCP_PATH}"
    def test_no_tunnel_running_is_not_an_error(self) -> None:
        def refused() -> str:
            raise ConnectionRefusedError(111, "Connection refused")
        assert discover({}, ngrok_reader=refused) is None
        assert discover({PUBLIC_URL_ENV: "   "}, ngrok_reader=refused) is None
    def test_discovery_can_be_switched_off_entirely(self) -> None:
        assert discover({}, ngrok_reader=None) is None
    def test_a_running_agent_with_no_usable_tunnel_is_an_error(self) -> None:
        with pytest.raises(NotPublicError):
            discover({}, ngrok_reader=lambda: '{"tunnels": []}')
