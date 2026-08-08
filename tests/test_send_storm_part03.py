from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_send_storm")).items() if not k.startswith("__")})

class TestTheAccountIsWorthMoreThanTheReport:
    def test_the_lock_names_what_it_saw(self, tmp_path: Path) -> None:
        api = CountingApi()
        gate = gatekeeper(tmp_path, Clock())
        run_storm(gate, api)
        assert gate.detector.locked
        assert gate.detector.reason(), "a lock with no reason tells nobody anything"
    def test_recovery_requires_a_person(self, tmp_path: Path) -> None:
        api = CountingApi()
        clock = Clock()
        gate = gatekeeper(tmp_path, clock)
        run_storm(gate, api)
        assert gate.detector.locked
        gate.detector.reset()
        gate.quota.reset()
        clock.at += 600.0  # and enough quiet time to have earned a token back
        assert run_storm(gate, api, iterations=50).sent > 0, "reset should restore service"
