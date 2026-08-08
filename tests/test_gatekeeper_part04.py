from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_gatekeeper")).items() if not k.startswith("__")})

class TestAttemptsAreRecordedSeparately:
    def test_recording_is_not_part_of_admission(self, tmp_path: Path) -> None:
        gate = gatekeeper(tmp_path)
        gate.admit()
        assert gate.detector.recent == []
    def test_recording_feeds_the_detector(self, tmp_path: Path) -> None:
        gate = gatekeeper(tmp_path)
        gate.admit()
        gate.record_attempt()
        assert len(gate.detector.recent) == 1
