from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_barriers")).items() if not k.startswith("__")})

class TestBeliefWeightedValue:
    @staticmethod
    def belief_over(state: BoardState, hot: dict[tuple[int, int], float]) -> Belief:
        belief = Belief.uniform(state)
        belief.update(hot)
        return belief
    def test_without_a_belief_map_the_raw_count_is_used(self) -> None:
        state = board((3, 3), (5, 5))
        assert score_placement(state, (3, 3), AXES, (5, 5)).value == 1.0
    def test_belief_scales_the_reduction(self) -> None:
        state = board((1, 1), (0, 0), grid_size=3, barriers={(0, 1)})
        belief = self.belief_over(state, {(0, 0): 9.0})
        scored = score_placement(state, (1, 0), AXES, (0, 0), belief)
        assert scored.escape_reduction == 7
        assert scored.severed_belief is not None and scored.severed_belief > 0.0
        assert scored.value == pytest.approx(7 * scored.severed_belief)
    def test_sealing_an_empty_region_is_worth_little(self) -> None:
        walls = frozenset({(0, 2), (1, 2), (3, 2), (4, 2), (5, 2), (6, 2)})
        state = board((2, 1), (2, 5), barriers=walls)
        belief = self.belief_over(state, {(2, 5): 40.0, (2, 6): 20.0})
        raw = score_placement(state, (2, 1), AXES, (2, 5))
        weighted = score_placement(state, (2, 1), AXES, (2, 5), belief)
        assert raw.escape_reduction == weighted.escape_reduction == 14
        assert weighted.severed_belief is not None and weighted.severed_belief < 0.2
        assert weighted.value < raw.value / 5, "cutting 14 empty cells should collapse"
    def test_where_the_mass_sits_decides_between_equal_cuts(self) -> None:
        walls = frozenset({(0, 2), (1, 2), (3, 2), (4, 2), (5, 2), (6, 2)})
        state = board((2, 1), (2, 5), barriers=walls)
        thief_is_left = self.belief_over(state, {(2, 0): 60.0, (1, 1): 20.0})
        thief_is_right = self.belief_over(state, {(2, 5): 40.0, (2, 6): 20.0})
        rich = score_placement(state, (2, 1), AXES, (2, 5), thief_is_left)
        poor = score_placement(state, (2, 1), AXES, (2, 5), thief_is_right)
        assert rich.escape_reduction == poor.escape_reduction == 14
        assert rich.value > poor.value * 4
    def test_the_sealed_cell_counts_even_when_nothing_is_cut_off(self) -> None:
        state = board((3, 3), (3, 4))
        belief = self.belief_over(state, {(3, 4): 40.0})
        scored = score_placement(state, (3, 4), AXES, (3, 4), belief)
        assert scored.severed_belief is not None
        assert scored.severed_belief > 0.3
    def test_a_uniform_belief_does_not_reorder_anything(self) -> None:
        state = board((3, 3), (5, 5))
        flat = Belief.uniform(state)
        assert [s.at for s in rank_placements(state, AXES, (5, 5), flat)] == [
            s.at for s in rank_placements(state, AXES, (5, 5))
        ]
    def test_the_weight_is_reported_in_the_log(self) -> None:
        state = board((1, 1), (0, 0), grid_size=3, barriers={(0, 1)})
        belief = self.belief_over(state, {(0, 0): 9.0})
        assert "belief-" in str(score_placement(state, (1, 0), AXES, (0, 0), belief))
    def test_the_vetoes_are_unaffected_by_belief(self) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(0, 1), (1, 0)})
        belief = self.belief_over(state, {(2, 2): 9.0})
        only = rank_placements(state, AXES, (2, 2), belief)[0]
        assert only.immobilises and not only.permitted
    def test_a_win_is_still_taken_regardless_of_belief(self) -> None:
        state = board((3, 3), (3, 4))
        assert winning_placement(state, AXES) == (3, 4)
