from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_outcome")).items() if not k.startswith("__")})

class TestEnclosureCapture:
    def test_open_board_is_not_enclosure(self) -> None:
        assert not is_enclosure_capture(make(), AXES)
    def test_all_four_neighbours_sealed_is_capture(self) -> None:
        state = make(thief=(3, 3), barriers=frozenset({(2, 3), (4, 3), (3, 2), (3, 4)}))
        assert is_enclosure_capture(state, AXES)
    def test_three_sealed_is_not_yet(self) -> None:
        state = make(thief=(3, 3), barriers=frozenset({(2, 3), (4, 3), (3, 2)}))
        assert not is_enclosure_capture(state, AXES)
    def test_board_edges_count_as_walls(self) -> None:
        state = make(cop=(6, 6), thief=(0, 0), barriers=frozenset({(1, 0), (0, 1)}))
        assert is_enclosure_capture(state, AXES)
    def test_edge_thief_needs_three(self) -> None:
        state = make(cop=(6, 6), thief=(0, 3), barriers=frozenset({(0, 2), (0, 4), (1, 3)}))
        assert is_enclosure_capture(state, AXES)
    def test_stay_remains_legal_under_enclosure(self) -> None:
        state = make(thief=(3, 3), barriers=frozenset({(2, 3), (4, 3), (3, 2), (3, 4)}))
        assert legal_moves(state, "thief", AXES) == ["STAY"]
        assert is_enclosure_capture(state, AXES)
    def test_a_literal_reading_would_never_fire(self) -> None:
        state = make(thief=(3, 3), barriers=frozenset({(2, 3), (4, 3), (3, 2), (3, 4)}))
        assert legal_moves(state, "thief", AXES) != []
    def test_holds_under_every_axis_convention(self) -> None:
        state = make(thief=(3, 3), barriers=frozenset({(2, 3), (4, 3), (3, 2), (3, 4)}))
        for corner in ORIGIN_CORNERS:
            assert is_enclosure_capture(state, AxisConvention(origin_corner=corner))
    def test_is_independent_of_the_other_captures(self) -> None:
        state = make(cop=(0, 0), thief=(3, 3), barriers=frozenset({(2, 3), (4, 3), (3, 2), (3, 4)}))
        assert is_enclosure_capture(state, AXES)
        assert not is_capture_by_overlap(state)
        assert not is_trapping_capture(state)
