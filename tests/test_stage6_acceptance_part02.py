from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage6_acceptance")).items() if not k.startswith("__")})

class TestACorruptedRevealIsDetected:
    def test_a_move_changed_after_the_commitment_fails_the_audit(self) -> None:
        game = play(corrupt_at=4)
        result = audit_opponent(game.cop.match, game.thief_disclosure, game.states)
        assert result.verdict is Verdict.FORGED
        assert len(result.failures) == 1
        assert "step 4" in result.failures[0]
    def test_the_honest_steps_still_verify(self) -> None:
        game = play(corrupt_at=2)
        result = audit_opponent(game.cop.match, game.thief_disclosure, game.states)
        assert result.checked == STEPS
        assert len(result.failures) == 1
    def test_the_cop_side_is_unaffected_by_the_thiefs_corruption(self) -> None:
        game = play(corrupt_at=2)
        assert audit_opponent(game.thief.match, game.cop_disclosure, game.states).clean
    def test_the_failure_carries_arithmetic_the_other_side_can_run(self) -> None:
        game = play(corrupt_at=3)
        failure = audit_opponent(game.cop.match, game.thief_disclosure, game.states).failures[0]
        assert "committed" in failure and "produces" in failure
