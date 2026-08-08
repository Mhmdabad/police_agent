from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_series_length")).items() if not k.startswith("__")})

class TestTheRunnerPlaysExactlySixNumberedSubGames:
    def test_it_takes_its_length_from_the_agreed_parameters(self, tmp_path: Path) -> None:
        assert a_runner(tmp_path).sub_games == BOOK_SERIES
    def test_the_length_cannot_be_supplied_by_a_caller(self) -> None:
        assert "sub_games" not in inspect.signature(MatchRunner).parameters
        assert "sub_games" not in inspect.signature(open_match).parameters
    def test_a_series_is_six_sub_games_numbered_one_to_six(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        played: list[int] = []
        monkeypatch.setattr(
            MatchRunner,
            "play_sub_game",
            lambda self, number, timeout=30.0: played.append(number),
        )
        crossed = stub_boundaries(monkeypatch)
        a_runner(tmp_path).play_series()
        assert played == [1, 2, 3, 4, 5, 6]
        assert crossed == [2, 3, 4, 5, 6], "six sub-games are separated by five boundaries"
    def test_a_runner_on_deviating_parameters_plays_nothing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            MatchRunner,
            "play_sub_game",
            lambda self, number, timeout=30.0: pytest.fail("a deviation must not be played"),
        )
        runner = a_runner(tmp_path)
        runner.parameters = copy.deepcopy(parameters())
        runner.parameters[SERIES_SECTION][SERIES_KEY] = 1
        with pytest.raises(ConfigError, match="disqualifies the team"):
            runner.play_series()
