from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_dos_detector")).items() if not k.startswith("__")})

class TestTheLockExplainsItself:
    def test_it_records_why(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        with pytest.raises(DosDetected):
            for gap in (1.0, 4.0, 2.0, 9.0, 1.0, 5.0):
                clock.advance(gap)
                gate.record()
        assert "burst limit" in gate.reason()
    def test_the_exception_names_the_file_to_delete(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        with pytest.raises(DosDetected, match=r"delete .*\.locked_cop\.json"):
            for gap in (1.0, 4.0, 2.0, 9.0, 1.0, 5.0):
                clock.advance(gap)
                gate.record()
    def test_it_says_a_report_is_being_sacrificed(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        with pytest.raises(DosDetected, match="sacrificed to save the account"):
            for gap in (1.0, 4.0, 2.0, 9.0, 1.0, 5.0):
                clock.advance(gap)
                gate.record()
    def test_an_unreadable_lock_file_still_reads_as_locked(self, tmp_path: Path) -> None:
        (tmp_path / ".locked_cop.json").write_text("{half a wr")
        gate = detector(tmp_path)
        assert gate.locked
        assert "could not be read" in gate.reason()
        with pytest.raises(DosDetected):
            gate.check()
    def test_a_lock_file_that_is_not_an_object_still_locks(self, tmp_path: Path) -> None:
        (tmp_path / ".locked_cop.json").write_text("[]")
        assert detector(tmp_path).reason() == ""
        with pytest.raises(DosDetected):
            detector(tmp_path).check()
    def test_the_lock_file_is_owner_only(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        with pytest.raises(DosDetected):
            for gap in (1.0, 4.0, 2.0, 9.0, 1.0, 5.0):
                clock.advance(gap)
                gate.record()
        assert stat.S_IMODE(gate.path.stat().st_mode) == 0o600
