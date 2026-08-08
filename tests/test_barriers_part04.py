from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_barriers")).items() if not k.startswith("__")})

class TestRanking:
    def test_every_reachable_cell_is_a_candidate(self) -> None:
        ranked = rank_placements(board((3, 3), (5, 5)), AXES, (5, 5))
        assert {score.at for score in ranked} == {(3, 3), (2, 3), (4, 3), (3, 2), (3, 4)}
    def test_a_corner_cop_has_three_candidates_not_five(self) -> None:
        ranked = rank_placements(board((0, 0), (5, 5)), AXES, (5, 5))
        assert {score.at for score in ranked} == {(0, 0), (1, 0), (0, 1)}
    def test_already_sealed_cells_are_not_offered(self) -> None:
        state = board((3, 3), (5, 5), barriers={(3, 4)})
        assert (3, 4) not in {score.at for score in rank_placements(state, AXES, (5, 5))}
    def test_best_first(self) -> None:
        ranked = rank_placements(board((0, 1), (2, 2), grid_size=3), AXES, (2, 2))
        assert [score.total for score in ranked] == sorted(
            (score.total for score in ranked), reverse=True
        )
    def test_self_cutting_candidates_sink_to_the_bottom(self) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(1, 0)})
        ranked = rank_placements(state, AXES, (2, 2))
        assert ranked[-1].disconnects
    def test_ties_resolve_by_position_not_set_order(self) -> None:
        state = board((3, 3), (5, 5))
        first = rank_placements(state, AXES, (5, 5))
        again = rank_placements(replace(state, barriers=frozenset()), AXES, (5, 5))
        assert [score.at for score in first] == [score.at for score in again]
    def test_nothing_available_when_every_reachable_cell_is_sealed(self) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(0, 0), (0, 1), (1, 0)})
        assert rank_placements(state, AXES, (2, 2)) == []
        assert best_placement(state, AXES, (2, 2)) is None
    def test_best_placement_agrees_with_the_ranking(self) -> None:
        state = board((1, 1), (0, 0), grid_size=3, barriers={(0, 1)})
        assert best_placement(state, AXES, (0, 0)) == rank_placements(state, AXES, (0, 0))[0]
