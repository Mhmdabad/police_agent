from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestForgeryIsCaught:
    def test_a_move_changed_after_the_commitment_fails(self) -> None:
        match, disclosed, states = honest_match()
        match.steps[2].revealed_theirs = reveal(
            step=2, sender="thief", move="W", intent="truth", hint="hint 2"
        )
        result = audit_opponent(match, disclosed, states)
        assert result.verdict is Verdict.FORGED
        assert len(result.failures) == 1
        assert "step 2" in result.failures[0]
    def test_a_changed_hint_fails_too(self) -> None:
        match, disclosed, states = honest_match()
        match.steps[1].revealed_theirs = reveal(
            step=1, sender="thief", move="S", intent="truth", hint="a different story"
        )
        assert audit_opponent(match, disclosed, states).verdict is Verdict.FORGED
    def test_a_flipped_intent_fails(self) -> None:
        match, disclosed, states = honest_match()
        match.steps[1].revealed_theirs = reveal(
            step=1, sender="thief", move="S", intent="lie", hint="hint 1"
        )
        assert audit_opponent(match, disclosed, states).verdict is Verdict.FORGED
    def test_a_substituted_nonce_fails(self) -> None:
        match, disclosed, states = honest_match()
        swapped = FinalReveal("thief", {**disclosed.nonces, 3: "f" * 32}, WHEN)
        assert audit_opponent(match, swapped, states).verdict is Verdict.FORGED
    def test_the_failure_states_arithmetic_both_sides_can_run(self) -> None:
        match, disclosed, states = honest_match()
        match.steps[1].revealed_theirs = reveal(
            step=1, sender="thief", move="W", intent="truth", hint="hint 1"
        )
        failure = audit_opponent(match, disclosed, states).failures[0]
        assert "committed" in failure and "produces" in failure and "'W'" in failure
    def test_every_step_is_checked_rather_than_stopping_at_the_first(self) -> None:
        match, disclosed, states = honest_match()
        for step in (1, 3):
            match.steps[step].revealed_theirs = reveal(
                step=step, sender="thief", move="W", intent="truth", hint=f"hint {step}"
            )
        result = audit_opponent(match, disclosed, states)
        assert len(result.failures) == 2
        assert result.checked == 3
