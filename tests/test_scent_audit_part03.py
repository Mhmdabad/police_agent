from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_audit")).items() if not k.startswith("__")})

class TestForgedScentFailsTheAudit:
    def test_honest_play_audits_clean(self) -> None:
        assert audit_scent(START, AXES, OUR_ROLE, honest(THEIR_MOVES)) == ()
    def test_a_field_the_physics_never_produced_is_caught(self) -> None:
        plays = honest(THEIR_MOVES[:2])
        plays[1] = StepPlay(2, plays[1].ours, plays[1].theirs, snapshot_at(OUR_START))
        problems = audit_scent(START, AXES, OUR_ROLE, plays)
        assert len(problems) == 1
        assert problems[0].startswith("step 2:")
    def test_an_inflated_peak_is_caught(self) -> None:
        plays = honest(THEIR_MOVES[:1])
        forged = dict(plays[0].disclosed or {})
        forged["5,5"] = 0.9
        forged["4,5"] = 0.62
        plays[0] = StepPlay(1, plays[0].ours, plays[0].theirs, forged)
        assert audit_scent(START, AXES, OUR_ROLE, plays)
    def test_a_malformed_field_is_an_audit_failure_not_an_exception(self) -> None:
        plays = honest(THEIR_MOVES[:1])
        plays[0] = StepPlay(1, plays[0].ours, plays[0].theirs, {"99,99": float("nan")})
        problems = audit_scent(START, AXES, OUR_ROLE, plays)
        assert len(problems) == 1
        assert "step 1" in problems[0]
    def test_an_absent_field_is_refused_rather_than_excused(self) -> None:
        plays = honest(THEIR_MOVES[:1])
        plays[0] = StepPlay(1, plays[0].ours, plays[0].theirs, None)
        problems = audit_scent(START, AXES, OUR_ROLE, plays)
        assert len(problems) == 1
        assert "no scent" in problems[0]
    def test_an_absent_field_is_tolerated_only_by_explicit_agreement(self) -> None:
        plays = honest(THEIR_MOVES[:1])
        plays[0] = StepPlay(1, plays[0].ours, plays[0].theirs, None)
        assert audit_scent(START, AXES, OUR_ROLE, plays, require_bound=False) == ()
    def test_a_move_the_board_forbids_is_an_audit_failure(self) -> None:
        plays = [StepPlay(1, MoveAction("STAY"), MoveAction(THEIR_MOVES[0]), None)]  # type: ignore[arg-type]
        problems = audit_scent(board_with(CORNERED), AXES, OUR_ROLE, plays)
        assert len(problems) == 1
        assert "step 1" in problems[0]
    def test_every_step_is_reported_not_only_the_first(self) -> None:
        plays = honest(THEIR_MOVES[:2])
        plays = [StepPlay(p.step, p.ours, p.theirs, snapshot_at(OUR_START)) for p in plays]
        assert len(audit_scent(START, AXES, OUR_ROLE, plays)) == 2
