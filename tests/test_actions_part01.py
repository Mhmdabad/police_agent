from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_actions")).items() if not k.startswith("__")})

class TestExclusivityByConstruction:
    def test_an_action_is_one_variant_or_the_other(self) -> None:
        assert set(typing.get_args(Action)) == {MoveAction, PlaceBarrier}
    def test_moving_never_places_a_barrier(self) -> None:
        after = apply_action(make(), "cop", MoveAction("S"), AXES)
        assert after.barriers == frozenset()
        assert after.barriers_used == 0
    def test_placing_never_moves_the_cop(self) -> None:
        before = make(cop=(2, 2))
        after = apply_action(before, "cop", PlaceBarrier((2, 3)), AXES)
        assert after.cop == before.cop
        assert after.barriers == frozenset({(2, 3)})
    def test_placing_never_moves_the_thief_either(self) -> None:
        before = make()
        after = apply_action(before, "cop", PlaceBarrier((1, 0)), AXES)
        assert after.thief == before.thief
