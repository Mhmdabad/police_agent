from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_match")).items() if not k.startswith("__")})

class TestTheResultIsScoredFromWhatWasPlayed:
    def test_a_capture_scores_the_cop(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path)
        runner.outcomes.append(an_outcome(1, captured=True))
        result = runner.result("a" * 40, 0, agreed=False, repositories=REPOS)
        cop, thief = scores_for(Outcome.CAPTURE)
        assert result.sub_games[0].cop_score == cop
        assert result.sub_games[0].thief_score == thief
    def test_survival_scores_the_thief(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path)
        runner.outcomes.append(an_outcome(1))
        result = runner.result("a" * 40, 0, agreed=False, repositories=REPOS)
        assert (result.sub_games[0].cop_score, result.sub_games[0].thief_score) == scores_for(
            Outcome.SURVIVAL
        )
    def test_the_scores_come_from_appendix_f_not_from_here(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path)
        runner.outcomes.append(an_outcome(1, captured=True))
        result = runner.result("a" * 40, 0, agreed=False, repositories=REPOS)
        assert (result.cop_total, result.thief_total) == scores_for(Outcome.CAPTURE)
    def test_the_totals_add_up_across_sub_games(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path)
        runner.outcomes.extend([an_outcome(1, captured=True), an_outcome(2)])
        result = runner.result("a" * 40, 0, agreed=False, repositories=REPOS)
        capture, survival = scores_for(Outcome.CAPTURE), scores_for(Outcome.SURVIVAL)
        assert result.cop_total == capture[0] + survival[0]
        assert result.thief_total == capture[1] + survival[1]
    def test_the_steps_played_are_recorded(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path)
        runner.outcomes.append(an_outcome(1))
        result = runner.result("a" * 40, 0, agreed=False, repositories=REPOS)
        assert result.sub_games[0].steps == 2
    def test_agreement_has_no_default(self, tmp_path: Path) -> None:
        import inspect
        signature = inspect.signature(MatchRunner.result)
        assert signature.parameters["agreed"].default is inspect.Parameter.empty
    def test_a_result_is_not_agreed_just_because_we_played(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path)
        runner.outcomes.append(an_outcome(1))
        result = runner.result("a" * 40, 0, agreed=False, repositories=REPOS)
        assert result.to_dict()["result_agreed_with_opponent"] is False
    def test_the_commit_hash_reaches_every_sub_game(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path)
        runner.outcomes.extend([an_outcome(1), an_outcome(2)])
        result = runner.result("b" * 40, 0, agreed=False, repositories=REPOS)
        assert {entry.commit_hash for entry in result.sub_games} == {"b" * 40}
