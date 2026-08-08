from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_bluff")).items() if not k.startswith("__")})

class TestLying:
    def test_a_lie_reads_the_same_as_a_truth(self) -> None:
        truth = compose((5, 1), BOARD, (3, 3), random.Random(1))
        lie = compose(decoy((5, 1), BOARD), BOARD, (3, 3), random.Random(1))
        assert truth != lie
        assert truth.split()[0] == lie.split()[0]
    def test_the_decoy_is_far_from_the_truth(self) -> None:
        for cell in ((0, 0), (5, 1), (2, 3)):
            far = decoy(cell, BOARD)
            assert abs(far[0] - cell[0]) + abs(far[1] - cell[1]) >= BOARD.grid_size - 1
    def test_the_decoy_is_on_the_board(self) -> None:
        for cell in ((0, 0), (6, 6), (3, 3)):
            assert BOARD.in_bounds(decoy(cell, BOARD))
    def test_a_centre_cell_still_produces_a_distant_decoy(self) -> None:
        for cell in ((3, 3), (2, 3), (3, 4)):
            far = decoy(cell, BOARD)
            assert BOARD.in_bounds(far)
            assert abs(far[0] - cell[0]) + abs(far[1] - cell[1]) >= BOARD.grid_size - 1
    def test_it_is_stable_under_ties(self) -> None:
        assert decoy((3, 3), BOARD) == decoy((3, 3), BOARD)
