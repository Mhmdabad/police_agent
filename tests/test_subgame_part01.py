from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_subgame")).items() if not k.startswith("__")})

class TestAWholeSubGameRuns:
    def test_it_plays_to_the_step_limit(self, tmp_path: Path) -> None:
        game, _, _ = a_subgame(tmp_path, max_steps=3)
        played = game.play()
        assert played.steps == 3
        assert played.reason == "step limit reached"
    def test_every_step_is_logged(self, tmp_path: Path) -> None:
        game, _, log = a_subgame(tmp_path, max_steps=3)
        game.play()
        assert sorted(log.entries) == [1, 2, 3]
    def test_the_board_advances(self, tmp_path: Path) -> None:
        game, _, _ = a_subgame(tmp_path, max_steps=3)
        before = game.state
        game.play()
        assert game.state != before, "three steps and nothing moved"
    def test_the_board_step_matches_the_ceremony_step(self, tmp_path: Path) -> None:
        game, _, log = a_subgame(tmp_path, max_steps=3)
        game.play()
        for number, entry in log.entries.items():
            assert entry.reveal is not None
            assert entry.reveal["state"]["step"] == number
    def test_the_four_phases_happen_in_order(self, tmp_path: Path) -> None:
        game, peer, _ = a_subgame(tmp_path, max_steps=2)
        game.play()
        assert peer.seen == ["commit", "ack", "reveal", "commit", "ack", "reveal", "final"]
