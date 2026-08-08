from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tradeoff")).items() if not k.startswith("__")})

class TestTheBrainWiresItTogether:
    def test_a_win_skips_the_comparison_entirely(self) -> None:
        walls = {(6, col) for col in range(7)} | {(5, col) for col in range(5)}
        state = board(cop=(3, 3), thief=(3, 4), barriers=walls)
        assert Budget(used=state.barriers_used).spendable == 0
        assert PoliceBrain(axes=AXES).decide(state, target=state.thief).action == PlaceBarrier(
            (3, 4)
        )
    def test_an_illegal_move_is_caught_before_it_is_weighed(self) -> None:
        class Rogue(PoliceBrain):
            def _pick_move(self, state: BoardState, **context: object) -> str:  # type: ignore[override]
                return "N"
        with pytest.raises(Exception, match="not among"):
            state = board(cop=(0, 0), thief=(3, 3))
            Rogue(axes=AXES).decide(state, target=state.thief)
    def test_concentration_defaults_to_the_uninformative_prior(self) -> None:
        assert PoliceBrain(axes=AXES).concentration() == 0.0
    def test_a_supplied_concentration_is_used(self) -> None:
        assert PoliceBrain(axes=AXES).concentration(concentration=0.25) == 0.25
    def test_a_nonsense_concentration_falls_back_rather_than_crashing(self) -> None:
        assert PoliceBrain(axes=AXES).concentration(concentration="soon") == 0.0
