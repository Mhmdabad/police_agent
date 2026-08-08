from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_replay")).items() if not k.startswith("__")})

class TestTheReplayObject:
    def test_a_replay_with_no_steps_is_refused_at_construction(self) -> None:
        with pytest.raises(ReplayError, match="no steps cannot be replayed"):
            Replay(game_id="g", sub_game=1, role="police", steps=())
