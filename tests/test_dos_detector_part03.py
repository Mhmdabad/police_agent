from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_dos_detector")).items() if not k.startswith("__")})

class TestTheMetronomeTrigger:
    def test_perfectly_even_spacing_locks(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        with pytest.raises(DosDetected, match="a loop's cadence"):
            for _ in range(METRONOME_RUN + 1):
                clock.advance(30.0)
                gate.record()
    def test_it_is_regularity_not_volume(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        with pytest.raises(DosDetected) as raised:
            for _ in range(METRONOME_RUN + 1):
                clock.advance(45.0)
                gate.record()
        assert "burst limit" not in str(raised.value)
    def test_a_slow_relentless_loop_is_caught(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        with pytest.raises(DosDetected, match="cadence"):
            for _ in range(METRONOME_RUN + 1):
                clock.advance(300.0)
                gate.record()
    def test_the_cadence_history_outlives_the_burst_window(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        clock.advance(300.0)
        gate.record()
        clock.advance(300.0)
        gate.record()
        assert len(gate.recent) == 2, "both are older than the 60s burst window"
    def test_irregular_spacing_at_the_same_volume_does_not_lock(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        for gap in (30.0, 44.0, 31.0, 90.0, 37.0):
            clock.advance(gap)
            gate.record()
        assert not gate.locked
    def test_a_run_one_short_does_not_lock(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        for _ in range(METRONOME_RUN):
            clock.advance(45.0)
            gate.record()
        assert not gate.locked
    def test_a_small_jitter_is_still_mechanical(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        with pytest.raises(DosDetected, match="cadence"):
            for gap in (45.0, 45.4, 44.8, 45.2, 45.1):
                clock.advance(gap)
                gate.record()
    def test_sends_in_the_same_instant_are_mechanical(self, tmp_path: Path) -> None:
        gate = detector(tmp_path, Clock())
        with pytest.raises(DosDetected):
            for _ in range(METRONOME_RUN + 1):
                gate.record()
