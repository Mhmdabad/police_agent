from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tunnel")).items() if not k.startswith("__")})

class TestPublicEndpoint:
    def test_it_normalises_on_construction(self) -> None:
        assert PublicEndpoint(f"{PUBLIC}/").url == f"{PUBLIC}{MCP_PATH}"
    def test_it_reports_host_and_tls(self) -> None:
        endpoint = PublicEndpoint(PUBLIC)
        assert endpoint.host == "a1b2c3d4.ngrok-free.app"
        assert endpoint.secure
    def test_http_is_recorded_not_refused(self) -> None:
        assert not PublicEndpoint("http://tunnel.localtonet.com").secure
    def test_it_refuses_the_loopback_address_we_developed_against(self) -> None:
        with pytest.raises(NotPublicError, match="not reachable from another machine"):
            PublicEndpoint("http://127.0.0.1:8801/mcp")
    def test_it_refuses_a_lan_address_that_only_works_on_one_desk(self) -> None:
        with pytest.raises(NotPublicError):
            PublicEndpoint("http://192.168.1.10:8801/mcp")
    def test_it_is_frozen_so_an_advertised_address_cannot_be_edited_later(self) -> None:
        endpoint = PublicEndpoint(PUBLIC)
        with pytest.raises(AttributeError):
            endpoint.url = "http://127.0.0.1:8801/mcp"  # type: ignore[misc]
