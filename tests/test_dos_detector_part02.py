from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_dos_detector")).items() if not k.startswith("__")})

class TestTheBurstTrigger:
    def test_too_many_inside_the_window_locks(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        with pytest.raises(DosDetected, match="over the burst limit"):
            for gap in (1.0, 4.0, 2.0, 9.0, 1.0, 5.0):
                clock.advance(gap)
                gate.record()
    def test_the_limit_is_far_under_what_the_bucket_would_allow(self) -> None:
        assert BURST_LIMIT < 30
    def test_the_lock_survives_the_object(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        with pytest.raises(DosDetected):
            for gap in (1.0, 4.0, 2.0, 9.0, 1.0, 5.0):
                clock.advance(gap)
                gate.record()
        assert detector(tmp_path).locked, "a fresh process must still find the door shut"
