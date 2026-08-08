from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_lock_negotiation")).items() if not k.startswith("__")})

class TestBothPeersCanNegotiateAtOnce:
    def test_neither_side_waits_for_the_other_to_go_first(self, wire: tuple[Side, Side]) -> None:
        done = both_lock(wire, timeout=BRIEF)
        assert [type(value) for value in done.values()] == [ScentAgreement] * 2, done
    def test_a_repeated_series_of_gates_never_stalls(self, wire: tuple[Side, Side]) -> None:
        for _ in range(3):
            assert set(both_lock(wire, timeout=BRIEF).values()) == {our_lock()}
    def test_the_config_gate_and_the_lock_run_back_to_back(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        def whole_negotiation(side: Side) -> ScentAgreement:
            side.orchestrator.agree_config(parameters(), game_uid=GAME_UID, timeout=PATIENCE)
            return side.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=PATIENCE)
        done = concurrently(
            {"ours": lambda: whole_negotiation(ours), "theirs": lambda: whole_negotiation(theirs)}
        )
        assert done == {"ours": our_lock(), "theirs": our_lock()}
