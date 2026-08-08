from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_send_storm")).items() if not k.startswith("__")})

class TestTheStormIsStopped:
    def test_it_does_not_run_to_completion(self, tmp_path: Path) -> None:
        api = CountingApi()
        storm = run_storm(gatekeeper(tmp_path, Clock()), api)
        assert storm.stopped_by, "the loop ran 4000 times and nothing objected"
        assert storm.attempts < STORM
    def test_almost_nothing_reaches_the_api(self, tmp_path: Path) -> None:
        api = CountingApi()
        run_storm(gatekeeper(tmp_path, Clock()), api)
        assert api.count <= 6, f"{api.count} messages reached the API"
    def test_nothing_reaches_the_api_after_the_gates_trip(self, tmp_path: Path) -> None:
        api = CountingApi()
        clock = Clock()
        gate = gatekeeper(tmp_path, clock)
        run_storm(gate, api)
        reached = api.count
        for _ in range(500):
            with pytest.raises((Rejected, DosDetected)):
                if gate.admit() is None:
                    gate.record_attempt()
                    api.send({"raw": "x"})
        assert api.count == reached, "the pipeline reopened after tripping"
    def test_a_fresh_process_is_still_blocked(self, tmp_path: Path) -> None:
        api = CountingApi()
        run_storm(gatekeeper(tmp_path, Clock()), api)
        reached = api.count
        restarted = gatekeeper(tmp_path, Clock())
        second = run_storm(restarted, api, iterations=500)
        assert second.sent == 0
        assert api.count == reached
