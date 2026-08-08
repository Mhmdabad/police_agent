from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_subgame")).items() if not k.startswith("__")})

class TestCaptureEndsIt:
    def test_the_loop_stops_on_capture(self, tmp_path: Path) -> None:
        start = board(grid=4, cop=(2, 2), thief=(2, 2))
        game, _, _ = a_subgame(tmp_path, max_steps=6, state=start)
        played = game.play()
        assert played.captured
        assert played.reason == "capture"
        assert played.steps < 6
    def test_it_still_discloses_every_nonce(self, tmp_path: Path) -> None:
        start = board(grid=4, cop=(2, 2), thief=(2, 2))
        game, _, log = a_subgame(tmp_path, max_steps=6, state=start)
        game.play()
        assert log.unopened() == []
    def test_survival_is_the_other_outcome(self, tmp_path: Path) -> None:
        game, _, _ = a_subgame(tmp_path, max_steps=2)
        assert game.play().thief_survived
