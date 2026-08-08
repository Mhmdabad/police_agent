from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_dos_detector")).items() if not k.startswith("__")})

class TestItWatchesAttemptsNotSuccesses:
    def test_a_loop_that_fails_every_time_is_still_caught(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        caught = 0
        for gap in (1.0, 4.0, 2.0, 9.0, 1.0, 5.0):
            clock.advance(gap)
            try:
                gate.record()
            except DosDetected:
                caught += 1
                break
            caught += 0
        assert caught == 1 and gate.locked
    def test_the_lock_is_written_before_the_exception(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        for gap in (1.0, 4.0, 2.0, 9.0, 1.0, 5.0):
            clock.advance(gap)
            with contextlib.suppress(DosDetected):
                gate.record()
        assert detector(tmp_path).locked
