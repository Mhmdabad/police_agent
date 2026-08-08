from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_subgame")).items() if not k.startswith("__")})

class TestTheOpponentIsAudited:
    def test_an_honest_opponent_audits_clean(self, tmp_path: Path) -> None:
        game, _, _ = a_subgame(tmp_path, max_steps=3)
        played = game.play()
        assert played.opponent_played_fairly, str(played.audit)
        assert played.audit.checked == 3
    def test_a_corrupted_reveal_is_caught_here(self, tmp_path: Path) -> None:
        game, _, _ = a_subgame(tmp_path, StandInOpponent(corrupt_at=2), max_steps=3)
        played = game.play()
        assert not played.opponent_played_fairly
        assert played.audit.verdict is Verdict.FORGED
    def test_the_finding_names_the_step_and_the_arithmetic(self, tmp_path: Path) -> None:
        game, _, _ = a_subgame(tmp_path, StandInOpponent(corrupt_at=2), max_steps=3)
        failures = game.play().audit.failures
        assert "step 2" in failures[0]
        assert "produces" in failures[0]
    def test_a_forgery_does_not_stay_local(self, tmp_path: Path) -> None:
        game, _, _ = a_subgame(tmp_path, StandInOpponent(corrupt_at=2), max_steps=3)
        failures = game.play().audit.failures
        assert sorted(f.split(":")[0] for f in failures) == [
            "step 2",
            "step 2",
            "step 3",
            "step 3",
        ]
    def test_every_step_is_still_checked(self, tmp_path: Path) -> None:
        game, _, _ = a_subgame(tmp_path, StandInOpponent(corrupt_at=2), max_steps=3)
        assert game.play().audit.checked == 3
    def test_the_board_each_step_was_sealed_against_is_kept(self, tmp_path: Path) -> None:
        game, _, _ = a_subgame(tmp_path, max_steps=3)
        game.play()
        assert sorted(game.sealed_states) == [1, 2, 3]
        assert game.sealed_states[2].step == 2
    def test_an_opponent_who_disclosed_nothing_is_unverifiable(self, tmp_path: Path) -> None:
        game, _, _ = a_subgame(tmp_path, max_steps=1)
        game._one_step(1)  # noqa: SLF001
        result = game.audit()
        assert result.verdict is Verdict.FORGED
        assert "unverifiable rather than proven" in result.failures[0]
