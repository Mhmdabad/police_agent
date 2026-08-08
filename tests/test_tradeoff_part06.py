from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tradeoff")).items() if not k.startswith("__")})

class TestTheNegotiatedQuotaIsHonoured:
    def test_the_policy_budgets_against_the_brains_limit_not_the_book(self) -> None:
        state = board(cop=(2, 1), thief=(2, 5), barriers=CORRIDOR)
        assert state.barriers_used == 6
        assert weigh(state, AXES, (2, 5), "E", max_barriers=14).place
        assert not weigh(state, AXES, (2, 5), "E", max_barriers=6).place
    def test_the_brain_falls_through_to_moving(self) -> None:
        state = board(cop=(2, 1), thief=(2, 5), barriers=CORRIDOR)
        assert isinstance(
            PoliceBrain(axes=AXES).decide(state, target=state.thief).action, PlaceBarrier
        )
        spent = PoliceBrain(axes=AXES, max_barriers=6).decide(state, target=state.thief).action
        assert isinstance(spent, MoveAction)
    def test_a_raised_quota_is_spendable_once_it_clears_the_reserve(self) -> None:
        walls = CORRIDOR | {(6, col) for col in range(4)}
        state = board(cop=(2, 1), thief=(2, 5), barriers=walls)
        assert state.barriers_used == 9
        assert not weigh(state, AXES, (2, 5), "E", max_barriers=12).place
        assert weigh(state, AXES, (2, 5), "E", max_barriers=13).place
        assert Budget(used=9, limit=12).spendable == 0
        assert Budget(used=9, limit=13).spendable == 1
    def test_a_win_respects_it_too(self) -> None:
        walls = frozenset({(6, col) for col in range(7)})
        state = board(cop=(3, 3), thief=(3, 4), barriers=walls)
        assert PoliceBrain(axes=AXES).decide(state, target=state.thief).action == PlaceBarrier(
            (3, 4)
        )
        assert isinstance(
            PoliceBrain(axes=AXES, max_barriers=7).decide(state, target=state.thief).action,
            MoveAction,
        )
