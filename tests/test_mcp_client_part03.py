from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mcp_client")).items() if not k.startswith("__")})

class TestSettings:
    def test_is_frozen(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            SETTINGS.opponent_url = "x"  # type: ignore[misc]
    def test_empty_url_is_refused(self) -> None:
        with pytest.raises(ValueError, match="opponent_url must be set"):
            ClientSettings(opponent_url="")
    @pytest.mark.parametrize("timeout", [0, -1.0])
    def test_non_positive_timeout_is_refused(self, timeout: float) -> None:
        with pytest.raises(ValueError, match="response_timeout_sec"):
            ClientSettings(opponent_url="u", response_timeout_sec=timeout)
    def test_negative_retries_are_refused(self) -> None:
        with pytest.raises(ValueError, match="max_retries"):
            ClientSettings(opponent_url="u", max_retries=-1)
    def test_defaults_follow_appendix_f(self) -> None:
        settings = ClientSettings(opponent_url=REMOTE)
        assert (settings.response_timeout_sec, settings.max_retries) == (30.0, 3)
        assert settings.retry_backoff_sec == 5.0
    def test_it_appends_the_endpoint_a_tunnel_never_prints(self) -> None:
        assert ClientSettings(opponent_url=REMOTE).opponent_url == f"{REMOTE}/mcp"
    def test_it_refuses_a_url_it_could_never_call(self) -> None:
        with pytest.raises(ValueError, match="must use one of"):
            ClientSettings(opponent_url="opponent.ngrok-free.app")
    def test_reads_the_shipped_private_config(self) -> None:
        path = Path(__file__).parents[1] / "config/police/game.toml"
        private = tomllib.loads(path.read_text())
        settings = ClientSettings.from_config(private["network"], environ={})
        assert settings.opponent_url.endswith("8802/mcp")
    def test_missing_opponent_url_is_refused(self) -> None:
        with pytest.raises(ValueError, match="must define opponent_url"):
            ClientSettings.from_config({}, environ={})
