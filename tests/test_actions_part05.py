from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_actions")).items() if not k.startswith("__")})

class TestApplyActionDispatch:
    def test_illegal_move_still_raises_from_the_move_path(self) -> None:
        with pytest.raises(IllegalMoveError):
            apply_action(make(cop=(0, 0)), "cop", MoveAction("N"), AXES)
    def test_honours_the_negotiated_convention(self) -> None:
        flipped = AxisConvention(origin_corner="bottom-left")
        assert apply_action(make(), "thief", MoveAction("N"), flipped).thief == (4, 3)
