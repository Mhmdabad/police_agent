from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_config_agreement")).items() if not k.startswith("__")})

class TestAMismatchAbortsBeforeAnySubGame:
    def test_both_sides_abort(self, wire: tuple[Side, Side]) -> None:
        done = both_run(wire, parameters(), altered())
        for role, outcome in done.items():
            assert isinstance(outcome, MatchAborted), f"{role} played on: {outcome!r}"
    def test_the_cause_is_an_illegal_action_on_both_sides(self, wire: tuple[Side, Side]) -> None:
        done = both_run(wire, parameters(), altered())
        assert [o.cause for o in done.values()] == [TechnicalLoss.ILLEGAL_ACTION] * 2
    def test_the_detail_names_both_digests(self, wire: tuple[Side, Side]) -> None:
        done = both_run(wire, parameters(), altered())
        detail = done["ours"].detail
        assert agreed_digest() in detail and config_sha256(altered()) in detail
    def test_not_one_sub_game_is_played(self, wire: tuple[Side, Side], tmp_path: Path) -> None:
        ours, theirs = fresh(wire)
        runner = a_runner(ours, altered(), tmp_path)
        done = concurrently(
            {"ours": lambda: runner.agree(timeout=PATIENCE), "theirs": gate(theirs, parameters())}
        )
        assert isinstance(done["ours"], MatchAborted)
        assert runner.outcomes == []
    def test_no_turn_ever_crosses_the_wire(self, wire: tuple[Side, Side], tmp_path: Path) -> None:
        ours, theirs = fresh(wire)
        runner = a_runner(ours, altered(), tmp_path)
        concurrently(
            {"ours": lambda: runner.agree(timeout=PATIENCE), "theirs": gate(theirs, parameters())}
        )
        assert theirs.inboxes.turns.empty()
        assert theirs.inboxes.accepted_turns == {}
