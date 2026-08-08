from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_dos_detector")).items() if not k.startswith("__")})

class TestOrdinaryUseDoesNotTrip:
    def test_a_single_send_is_fine(self, tmp_path: Path) -> None:
        gate = detector(tmp_path)
        gate.record()
        assert not gate.locked
    def test_a_match_worth_of_reports_is_fine(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        realistic(gate, clock, count=10)
        assert not gate.locked
    def test_a_few_sends_close_together_are_fine(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        for gap in (3.0, 11.0, 2.0):
            clock.advance(gap)
            gate.record()
        assert not gate.locked
    def test_the_burst_window_slides(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        for gap in (90.0, 140.0, 71.0, 205.0, 96.0, 133.0, 88.0):
            clock.advance(gap)
            gate.record()
        assert not gate.locked
