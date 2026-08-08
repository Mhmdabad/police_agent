from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tunnel")).items() if not k.startswith("__")})

class TestRehearsingAgainstOurselves:
    def test_loopback_is_allowed_here_and_nowhere_else(self) -> None:
        assert rehearsal_url({"PUBLIC_URL": "http://127.0.0.1:8801"}) == "http://127.0.0.1:8801/mcp"
        with pytest.raises(NotPublicError):
            PublicEndpoint("http://127.0.0.1:8801")
    def test_it_falls_back_to_this_agents_own_port(self) -> None:
        assert rehearsal_url({}, 8802) == "http://127.0.0.1:8802/mcp"
    def test_the_mcp_path_is_still_appended(self) -> None:
        assert rehearsal_url({"PUBLIC_URL": "http://localhost:8802"}).endswith("/mcp")
    def test_a_typo_is_still_a_typo(self) -> None:
        with pytest.raises(NotPublicError):
            rehearsal_url({"PUBLIC_URL": "127.0.0.1:8801"})
