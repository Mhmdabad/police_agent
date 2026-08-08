from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_outcome")).items() if not k.startswith("__")})

class TestTrappingCapture:
    def test_open_cell_is_not_a_trapping_capture(self) -> None:
        assert not is_trapping_capture(make())
    def test_barrier_under_the_thief_is_a_capture(self) -> None:
        assert is_trapping_capture(make(thief=(3, 3), barriers=frozenset({(3, 3)})))
    def test_barriers_elsewhere_do_not_trigger_it(self) -> None:
        state = make(thief=(3, 3), barriers=frozenset({(2, 3), (4, 3), (3, 2), (3, 4)}))
        assert not is_trapping_capture(state)
    def test_arises_from_a_real_placement(self) -> None:
        state = make(cop=(3, 2), thief=(3, 3))
        after = apply_action(state, "cop", PlaceBarrier((3, 3)), AXES)
        assert is_trapping_capture(after)
    def test_needs_the_cop_adjacent(self) -> None:
        assert (3, 3) not in {(0, 0), (1, 0), (0, 1)}
    def test_a_thief_can_never_move_onto_a_barrier(self) -> None:
        state = make(thief=(3, 3), barriers=frozenset({(2, 3)}))
        assert "N" not in legal_moves(state, "thief", AXES)
    def test_is_independent_of_overlap(self) -> None:
        state = make(cop=(0, 0), thief=(3, 3), barriers=frozenset({(3, 3)}))
        assert is_trapping_capture(state)
        assert not is_capture_by_overlap(state)
