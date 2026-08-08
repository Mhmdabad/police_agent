from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_dos_detector")).items() if not k.startswith("__")})

class TestTheLockDoesNotExpire:
    def test_check_keeps_refusing_however_long_you_wait(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        with pytest.raises(DosDetected):
            for gap in (1.0, 4.0, 2.0, 9.0, 1.0, 5.0):
                clock.advance(gap)
                gate.record()
        clock.advance(86_400.0)
        with pytest.raises(DosDetected, match="is locked"):
            gate.check()
    def test_recording_while_locked_refuses(self, tmp_path: Path) -> None:
        (tmp_path / ".locked_cop.json").write_text(json.dumps({"reason": "earlier"}))
        with pytest.raises(DosDetected):
            detector(tmp_path).record()
    def test_only_reset_clears_it(self, tmp_path: Path) -> None:
        gate = detector(tmp_path)
        (tmp_path / ".locked_cop.json").write_text(json.dumps({"reason": "earlier"}))
        gate.reset()
        assert not gate.locked
        gate.record()
    def test_reset_also_forgets_the_history(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        with pytest.raises(DosDetected):
            for gap in (1.0, 4.0, 2.0, 9.0, 1.0, 5.0):
                clock.advance(gap)
                gate.record()
        gate.reset()
        clock.advance(1.0)
        gate.record()
        assert not gate.locked
    def test_reset_on_an_unlocked_detector_is_harmless(self, tmp_path: Path) -> None:
        detector(tmp_path).reset()
