from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_series_length")).items() if not k.startswith("__")})

class TestTheCommandLineTakesItFromTheConfigRatherThanFromOne:
    def test_the_default_is_the_book_length(self) -> None:
        assert resolve_series_length(None, REPO / "config/game.json") == BOOK_SERIES
    def test_the_flag_carries_no_series_length_of_its_own(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(REPO)
        asked: list[int | None] = []
        def remember(requested: int | None, path: Path) -> int:
            asked.append(requested)
            return BOOK_SERIES
        monkeypatch.setattr("cop_agent.__main__.resolve_series_length", remember)
        main(["check"], environ=NO_TUNNEL)
        assert asked == [None]
    def test_check_reports_the_series_it_would_play(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.chdir(REPO)
        assert main(["check"], environ=NO_TUNNEL) == 0
        assert "6 sub-games" in capsys.readouterr().out
    def test_a_deviating_flag_stops_play_before_anything_starts(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(REPO)
        monkeypatch.setattr(
            "cop_agent.__main__.play", lambda *_: pytest.fail("a deviation must not reach play")
        )
        monkeypatch.setattr(
            "cop_agent.__main__.serve",
            lambda *_: pytest.fail("a deviation must not bind a socket"),
        )
        assert main(["play", "--game-id", "uoh26-x", "--sub-games", "3"], environ=PUBLIC) == 1
    def test_the_refusal_says_why_on_stderr(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.chdir(REPO)
        main(["play", "--game-id", "uoh26-x", "--sub-games", "1"], environ=PUBLIC)
        error = capsys.readouterr().err
        assert "disqualifies the team" in error
        assert "cannot start" in error
    def test_asking_for_six_is_not_an_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(REPO)
        reached: list[object] = []
        def played(*args: object) -> int:
            reached.append(args)
            return 0
        monkeypatch.setattr("cop_agent.__main__.play", played)
        assert main(["play", "--game-id", "uoh26-x", "--sub-games", "6"], environ=PUBLIC) == 0
        assert reached, "a request for the book length should have played"
    def test_a_deviating_shared_config_is_refused_before_the_socket(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        deviant = tmp_path / "game.json"
        config = copy.deepcopy(shipped())
        config[SERIES_SECTION][SERIES_KEY] = 1
        deviant.write_text(json.dumps(config))
        with pytest.raises(ConfigError, match="disqualifies the team"):
            resolve_series_length(None, deviant)
    def test_a_shared_config_that_is_absent_says_so(self, tmp_path: Path) -> None:
        with pytest.raises(StartupError, match="shared configuration"):
            resolve_series_length(None, tmp_path / "absent.json")
    def test_a_shared_config_that_is_not_json_says_so(self, tmp_path: Path) -> None:
        broken = tmp_path / "game.json"
        broken.write_text("{not json")
        with pytest.raises(StartupError, match="valid JSON"):
            resolve_series_length(None, broken)
    def test_serve_refuses_a_deviating_shared_config_too(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        deviant = tmp_path / "game.json"
        config = copy.deepcopy(shipped())
        config[SERIES_SECTION][SERIES_KEY] = 1
        deviant.write_text(json.dumps(config))
        monkeypatch.chdir(REPO)
        monkeypatch.setattr("cop_agent.__main__.SHARED_CONFIG", deviant)
        monkeypatch.setattr(
            "cop_agent.__main__.serve", lambda *_: pytest.fail("must not bind a socket")
        )
        assert main([], environ=NO_TUNNEL) == 1
    def test_the_private_config_cannot_shorten_the_series(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        private = tmp_path / "game.toml"
        private.write_text("num_games = 1\nsub_games = 1\n" + (REPO / CONFIG).read_text())
        monkeypatch.chdir(REPO)
        assert main(["check", "--config", str(private)], environ=NO_TUNNEL) == 0
        assert "6 sub-games" in capsys.readouterr().out
    def test_the_command_and_the_driver_read_one_shared_config(self) -> None:
        assert SHARED_CONFIG.as_posix() == "config/game.json"
        for module in (cli, driver):
            assert getattr(module, "SHARED_CONFIG") is SHARED_CONFIG  # noqa: B009
