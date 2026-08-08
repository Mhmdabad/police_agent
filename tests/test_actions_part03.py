from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_actions")).items() if not k.startswith("__")})

class TestOnlyTheCopPlaces:
    def test_thief_cannot_place_a_barrier(self) -> None:
        with pytest.raises(IllegalActionError, match="only the cop"):
            apply_action(make(), "thief", PlaceBarrier((3, 4)), AXES)
    def test_thief_may_still_move(self) -> None:
        assert apply_action(make(), "thief", MoveAction("N"), AXES).thief == (2, 3)
