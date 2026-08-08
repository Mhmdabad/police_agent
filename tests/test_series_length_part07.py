from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_series_length")).items() if not k.startswith("__")})

class TestTheEvidenceCountsSixSubGames:
    @staticmethod
    def a_played_series(tmp_path: Path) -> MatchRunner:
        runner = a_runner(tmp_path)
        runner.outcomes.extend(an_outcome(number) for number in range(1, BOOK_SERIES + 1))
        return runner
    def test_the_result_reports_every_sub_game(self, tmp_path: Path) -> None:
        result = self.a_played_series(tmp_path).result(
            "a" * 40, 0, agreed=False, repositories=REPOS
        )
        assert [entry.sub_game for entry in result.sub_games] == [1, 2, 3, 4, 5, 6]
    def test_the_totals_say_six_were_played(self, tmp_path: Path) -> None:
        result = self.a_played_series(tmp_path).result(
            "a" * 40, 0, agreed=False, repositories=REPOS
        )
        assert result.to_dict()["totals"]["sub_games_played"] == BOOK_SERIES
    def test_the_artefacts_agree_that_there_were_six(self, tmp_path: Path) -> None:
        runner = self.a_played_series(tmp_path)
        result = runner.result("a" * 40, 0, agreed=False, repositories=REPOS)
        artefacts = runner.artefacts(result)
        assert len(artefacts.configs) == BOOK_SERIES
        assert len(artefacts.logs) == BOOK_SERIES
        assert artefacts.check().coherent
    def test_the_written_set_is_one_config_and_one_log_per_sub_game(self, tmp_path: Path) -> None:
        runner = self.a_played_series(tmp_path)
        written = runner.write(runner.result("a" * 40, 0, agreed=False, repositories=REPOS))
        assert len([p for p in written if p.name.startswith("config_")]) == BOOK_SERIES
        assert len([p for p in written if p.name.startswith("log_")]) == BOOK_SERIES
        assert len(written) == BOOK_SERIES * 2 + 2
    def test_the_sub_games_are_numbered_in_the_filenames(self, tmp_path: Path) -> None:
        runner = self.a_played_series(tmp_path)
        written = runner.write(runner.result("a" * 40, 0, agreed=False, repositories=REPOS))
        assert {p.name for p in written if p.name.startswith("log_")} == {
            f"log_uoh26-s82kma9e_g{number:02d}.json" for number in range(1, BOOK_SERIES + 1)
        }
