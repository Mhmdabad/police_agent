from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_replay")).items() if not k.startswith("__")})

class TestNavigation:
    def test_it_starts_at_the_first_step(self, tmp_path: Path) -> None:
        replay = load(written(tmp_path))
        assert replay.current.step == 1
        assert replay.at_start and not replay.at_end
    def test_forward_and_back(self, tmp_path: Path) -> None:
        replay = load(written(tmp_path))
        assert replay.forward().step == 2
        assert replay.forward().step == 3
        assert replay.back().step == 2
    def test_it_clamps_at_the_end_rather_than_wrapping(self, tmp_path: Path) -> None:
        replay = load(written(tmp_path))
        for _ in range(20):
            replay.forward()
        assert replay.current.step == 4
        assert replay.at_end
    def test_it_clamps_at_the_start(self, tmp_path: Path) -> None:
        replay = load(written(tmp_path))
        for _ in range(20):
            replay.back()
        assert replay.current.step == 1
    def test_seeking_a_step_that_exists(self, tmp_path: Path) -> None:
        assert load(written(tmp_path)).seek(3).step == 3
    def test_seeking_a_step_that_does_not_is_named_not_clamped(self, tmp_path: Path) -> None:
        with pytest.raises(ReplayError, match=r"step 12 is not in this log"):
            load(written(tmp_path)).seek(12)
