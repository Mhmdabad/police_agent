from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_actions")).items() if not k.startswith("__")})

class TestPlacementRange:
    def test_centre_cop_reaches_own_cell_and_four_neighbours(self) -> None:
        cells = placement_range(make(cop=(3, 3)), AXES)
        assert cells == frozenset({(3, 3), (2, 3), (4, 3), (3, 2), (3, 4)})
    def test_corner_cop_loses_the_off_board_neighbours(self) -> None:
        assert placement_range(make(cop=(0, 0)), AXES) == frozenset({(0, 0), (1, 0), (0, 1)})
    def test_range_contains_no_diagonals(self) -> None:
        cells = placement_range(make(cop=(3, 3)), AXES)
        for diagonal in ((2, 2), (2, 4), (4, 2), (4, 4)):
            assert diagonal not in cells
    def test_may_seal_its_own_cell(self) -> None:
        assert place_barrier(make(cop=(3, 3)), (3, 3), AXES).is_barrier((3, 3))
    def test_may_seal_an_orthogonal_neighbour(self) -> None:
        assert place_barrier(make(cop=(3, 3)), (2, 3), AXES).is_barrier((2, 3))
    def test_refuses_a_distant_cell(self) -> None:
        with pytest.raises(IllegalActionError, match="out of reach"):
            place_barrier(make(cop=(0, 0)), (5, 5), AXES)
    def test_refuses_a_diagonal_neighbour(self) -> None:
        with pytest.raises(IllegalActionError, match="out of reach"):
            place_barrier(make(cop=(3, 3)), (2, 2), AXES)
    def test_refuses_two_cells_away(self) -> None:
        with pytest.raises(IllegalActionError, match="out of reach"):
            place_barrier(make(cop=(3, 3)), (1, 3), AXES)
    def test_range_follows_the_negotiated_convention(self) -> None:
        flipped = AxisConvention(origin_corner="bottom-right")
        assert placement_range(make(cop=(3, 3)), AXES) == placement_range(make(cop=(3, 3)), flipped)
    def test_trapping_placement_on_the_thief_is_in_range_when_adjacent(self) -> None:
        assert (3, 3) in placement_range(make(cop=(3, 2), thief=(3, 3)), AXES)
