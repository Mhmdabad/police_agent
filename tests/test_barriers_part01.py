from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_barriers")).items() if not k.startswith("__")})

class TestChainProgress:
    def test_open_ground_has_no_closed_sides(self) -> None:
        assert chain_progress(board((3, 3), (5, 5)), (3, 3), AXES) == 0
    def test_a_corner_supplies_two_sides_for_free(self) -> None:
        assert chain_progress(board((3, 3), (5, 5)), (0, 0), AXES) == 2
    def test_an_edge_supplies_one(self) -> None:
        assert chain_progress(board((3, 3), (5, 5)), (0, 3), AXES) == 1
    def test_an_existing_barrier_counts_the_same_as_the_edge(self) -> None:
        state = board((3, 3), (5, 5), barriers={(2, 2)})
        assert chain_progress(state, (2, 3), AXES) == 1
        assert chain_progress(state, (0, 3), AXES) == 1
    def test_sides_accumulate(self) -> None:
        state = board((3, 3), (5, 5), barriers={(0, 2), (1, 3)})
        assert chain_progress(state, (0, 3), AXES) == 3
