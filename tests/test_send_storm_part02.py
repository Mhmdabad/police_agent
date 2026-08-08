from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_send_storm")).items() if not k.startswith("__")})

class TestEachGateCanStopItAlone:
    def test_the_dos_detector_alone_stops_it(self, tmp_path: Path) -> None:
        api = CountingApi()
        clock = Clock()
        gate = gatekeeper(tmp_path, clock, limit=10_000)
        gate.limiter.bucket.capacity = 10_000.0
        gate.limiter.bucket._tokens = 10_000.0  # noqa: SLF001 - disabling the other gates
        storm = run_storm(gate, api)
        assert storm.stopped_by == "DosDetected"
        assert api.count < 10
    def test_the_quota_alone_stops_it(self, tmp_path: Path) -> None:
        api = CountingApi()
        clock = Clock()
        gate = gatekeeper(tmp_path, clock, limit=3)
        gate.detector.burst_limit = 10_000
        gate.detector.metronome_run = 10_000
        gate.limiter.bucket.capacity = 10_000.0
        gate.limiter.bucket._tokens = 10_000.0  # noqa: SLF001
        storm = run_storm(gate, api)
        assert storm.stopped_by == "Rejected"
        assert api.count == 3, "the ceiling is the ceiling"
    def test_the_bucket_alone_throttles_it(self, tmp_path: Path) -> None:
        api = CountingApi()
        gate = gatekeeper(tmp_path, Clock(step=0.0), limit=10_000)
        gate.detector.burst_limit = 10_000
        gate.detector.metronome_run = 10_000
        run_storm(gate, api, iterations=1000)
        assert api.count == 2, "only the initial burst capacity got through"
