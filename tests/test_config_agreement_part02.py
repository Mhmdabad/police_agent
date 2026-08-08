from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_config_agreement")).items() if not k.startswith("__")})

class TestBothPeersCanNegotiateAtOnce:
    def test_neither_side_waits_for_the_other_to_go_first(self, wire: tuple[Side, Side]) -> None:
        done = both_run(wire, parameters(), parameters(), timeout=BRIEF)
        assert [type(v) for v in done.values()] == [str, str], done
    def test_a_repeated_series_of_gates_never_stalls(self, wire: tuple[Side, Side]) -> None:
        for _ in range(3):
            done = both_run(wire, parameters(), parameters(), timeout=BRIEF)
            assert set(done.values()) == {agreed_digest()}
