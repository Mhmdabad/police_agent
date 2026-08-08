from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mcp_client")).items() if not k.startswith("__")})

class TestPointingAtTheOpponentsTunnel:
    def test_the_environment_overrides_the_committed_file(self) -> None:
        settings = ClientSettings.from_config(
            {"opponent_url": "http://127.0.0.1:8802/mcp"}, environ={OPPONENT_URL_ENV: REMOTE}
        )
        assert settings.opponent_url == f"{REMOTE}/mcp"
    def test_the_override_alone_is_enough(self) -> None:
        assert ClientSettings.from_config({}, environ={OPPONENT_URL_ENV: REMOTE}).opponent_url == (
            f"{REMOTE}/mcp"
        )
    @pytest.mark.parametrize("blank", ["", "   ", "\n"])
    def test_a_blank_override_falls_through_to_the_file(self, blank: str) -> None:
        settings = ClientSettings.from_config(
            {"opponent_url": "http://127.0.0.1:8802/mcp"}, environ={OPPONENT_URL_ENV: blank}
        )
        assert settings.opponent_url.endswith("8802/mcp")
    def test_a_bad_override_raises_rather_than_falling_back(self) -> None:
        with pytest.raises(ValueError):
            ClientSettings.from_config(
                {"opponent_url": "http://127.0.0.1:8802/mcp"},
                environ={OPPONENT_URL_ENV: "ftp://opponent"},
            )
    def test_it_reads_the_real_environment_when_none_is_given(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(OPPONENT_URL_ENV, REMOTE)
        assert ClientSettings.from_config({}).opponent_url == f"{REMOTE}/mcp"
    def test_the_committed_file_still_points_at_loopback(self) -> None:
        path = Path(__file__).parents[1] / "config/police/game.toml"
        private = tomllib.loads(path.read_text())
        assert private["network"]["opponent_url"].startswith("http://127.0.0.1:")
