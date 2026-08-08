from cop_agent.domain.belief import Belief
from cop_agent.domain.board import BoardState
from cop_agent.domain.foci import SWITCH_MARGIN, Commitment, foci
BOARD = BoardState(cop=(0, 0), thief=(6, 6), grid_size=7)
def split() -> Belief:
    belief = Belief.uniform(BOARD)
    belief.update({(6, 6): 9.0, (6, 5): 6.0, (0, 3): 8.0, (0, 2): 5.0})
    return belief
class TestFindingFoci:
    def test_a_uniform_prior_has_no_focus_at_all(self) -> None:
        assert foci(Belief.uniform(BOARD)) == []
    def test_a_contradiction_produces_two(self) -> None:
        clusters = foci(split())
        assert len(clusters) == 2
        assert {c.peak for c in clusters} == {(6, 6), (0, 3)}
    def test_they_are_ordered_by_mass(self) -> None:
        clusters = foci(split())
        assert clusters[0].mass >= clusters[1].mass
    def test_one_hill_is_one_focus_not_five(self) -> None:
        belief = Belief.uniform(BOARD)
        belief.update({(3, 3): 9.0, (2, 3): 6.0, (4, 3): 6.0, (3, 2): 6.0, (3, 4): 6.0})
        clusters = foci(belief)
        assert len(clusters) == 1
        assert clusters[0].peak == (3, 3)
        assert len(clusters[0].cells) == 5
    def test_diagonal_cells_are_not_adjacent(self) -> None:
        belief = Belief.uniform(BOARD)
        belief.update({(1, 1): 9.0, (2, 2): 9.0})
        assert len(foci(belief)) == 2
    def test_the_background_floor_is_the_uniform_share(self) -> None:
        belief = split()
        assert all(len(c.cells) < 10 for c in foci(belief))
        assert len(foci(belief, background=0.0)) == 1
    def test_it_is_stable_across_calls(self) -> None:
        belief = split()
        assert [c.peak for c in foci(belief)] == [c.peak for c in foci(belief)]
    def test_an_empty_belief_has_none(self) -> None:
        assert foci(Belief(grid_size=7)) == []
    def test_a_focus_reports_its_share(self) -> None:
        clusters = foci(split())
        assert 0.0 < clusters[0].mass < 1.0
        assert "holding" in str(clusters[0])
class TestCommitment:
    def test_it_picks_the_heavier_focus_first(self) -> None:
        assert Commitment().choose(split()) == (6, 6)
    def test_it_holds_through_a_challenge_that_does_not_clear_the_margin(self) -> None:
        belief = split()
        commitment = Commitment()
        assert commitment.choose(belief) == (6, 6)
        belief.update({(0, 3): 1.6})
        assert commitment.choose(belief) == (6, 6)
        assert commitment.switches == 0
        assert commitment.held == 2
    def test_it_switches_once_the_margin_is_cleared(self) -> None:
        belief = split()
        commitment = Commitment()
        commitment.choose(belief)
        belief.update({(0, 3): 20.0})
        assert commitment.choose(belief) == (0, 3)
        assert commitment.switches == 1
        assert commitment.held == 1
    def test_the_margin_is_a_ratio_not_a_difference(self) -> None:
        assert SWITCH_MARGIN > 1.0
    def test_it_follows_a_focus_that_drifts_rather_than_abandoning_it(self) -> None:
        belief = Belief.uniform(BOARD)
        belief.update({(3, 3): 9.0, (3, 4): 8.0})
        commitment = Commitment()
        assert commitment.choose(belief) == (3, 3)
        belief.update({(3, 4): 3.0})
        assert commitment.choose(belief) == (3, 4)
        assert commitment.switches == 0
    def test_it_re_seeds_when_the_committed_focus_disappears(self) -> None:
        belief = split()
        commitment = Commitment()
        commitment.choose(belief)
        belief.update({(6, 6): 0.0, (6, 5): 0.0})
        assert commitment.choose(belief) == (0, 3)
    def test_no_belief_means_no_commitment(self) -> None:
        commitment = Commitment()
        assert commitment.choose(Belief.uniform(BOARD)) is None
        assert commitment.peak is None
    def test_a_long_run_does_not_oscillate(self) -> None:
        belief = split()
        commitment = Commitment()
        picks = []
        for turn in range(12):
            belief.update({(6, 6): 2.0} if turn % 2 else {(0, 3): 2.0})
            picks.append(commitment.choose(belief))
        assert commitment.switches <= 1, f"oscillated: {picks}"
    def test_a_genuine_shift_is_still_followed(self) -> None:
        belief = split()
        commitment = Commitment()
        assert commitment.choose(belief) == (6, 6)
        picks = []
        for _ in range(4):
            belief.update({(0, 3): 5.0, (0, 2): 3.0})
            picks.append(commitment.choose(belief))
        assert picks[-1] == (0, 3)
        assert commitment.switches == 1, f"switched more than once: {picks}"
    def test_it_reports_what_it_is_doing(self) -> None:
        commitment = Commitment()
        commitment.choose(split())
        assert "committed to (6, 6)" in str(commitment)
        assert "0 switch" in str(commitment)
    def test_an_empty_belief_clears_the_commitment(self) -> None:
        commitment = Commitment()
        commitment.choose(split())
        assert commitment.choose(Belief(grid_size=7)) is None
        assert commitment.peak is None
