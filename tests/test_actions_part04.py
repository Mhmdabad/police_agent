from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_actions")).items() if not k.startswith("__")})

class TestPlaceBarrier:
    def test_returns_a_new_state(self) -> None:
        before = make()
        after = place_barrier(before, (1, 0), AXES)
        assert after is not before
        assert before.barriers == frozenset()
    def test_rejects_an_off_board_cell(self) -> None:
        with pytest.raises(IllegalActionError, match="off a 7 board"):
            place_barrier(make(), (9, 9), AXES)
    def test_adds_to_existing_barriers(self) -> None:
        state = make(barriers=frozenset({(1, 1)}))
        assert place_barrier(state, (0, 1), AXES).barriers == frozenset({(1, 1), (0, 1)})
    def test_preserves_step_and_positions(self) -> None:
        before = make(step=5)
        after = place_barrier(before, (1, 0), AXES)
        assert (after.step, after.cop, after.thief) == (5, before.cop, before.thief)
