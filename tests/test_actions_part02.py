from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_actions")).items() if not k.startswith("__")})

class TestActionTypes:
    def test_actions_are_frozen(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            MoveAction("N").move = "S"  # type: ignore[misc]
        with pytest.raises(dataclasses.FrozenInstanceError):
            PlaceBarrier((1, 1)).at = (2, 2)  # type: ignore[misc]
    def test_actions_are_comparable(self) -> None:
        assert MoveAction("N") == MoveAction("N")
        assert PlaceBarrier((1, 1)) == PlaceBarrier((1, 1))
    def test_variants_are_never_equal(self) -> None:
        move: object = MoveAction("N")
        place: object = PlaceBarrier((1, 1))
        assert move != place
