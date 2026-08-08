from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_match")).items() if not k.startswith("__")})

class TestWhatTheMatchConcludesAboutTheOpponent:
    def test_a_clean_series_is_clean(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path)
        runner.outcomes.extend([an_outcome(1), an_outcome(2)])
        assert runner.opponent_played_fairly
        assert runner.failures() == []
    def test_one_forged_sub_game_taints_the_match(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path)
        runner.outcomes.extend([an_outcome(1), an_outcome(2, clean=False)])
        assert not runner.opponent_played_fairly
    def test_the_findings_name_their_sub_game(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path)
        runner.outcomes.extend([an_outcome(1), an_outcome(2, clean=False)])
        assert runner.failures() == [
            "sub-game 2: step 2: committed abc… but the revealed move produces def…"
        ]
    def test_an_empty_match_is_vacuously_fair(self, tmp_path: Path) -> None:
        assert a_runner(tmp_path).opponent_played_fairly
