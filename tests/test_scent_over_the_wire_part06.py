from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_over_the_wire")).items() if not k.startswith("__")})

class TestTheScriptIsPlayable:
    def test_every_scripted_move_is_a_real_move(self) -> None:
        assert all(move in _moves() for side in SCRIPT.values() for move in side)
