import pytest
from cop_agent.domain.credibility import (
    CONTRADICTION,
    FRESH_TRACE,
    MIN_RELIABILITY,
    Credibility,
    Verdict,
    check,
    true_source,
)
from cop_agent.domain.inference import MAX_RELIABILITY as MAX_TRUST
class TestTheBooksWorkedExample:
    NORTH = {(0, 3): 1.0}
    SOUTH_EAST = {(6, 6): 0.9, (6, 5): 0.62, (5, 6): 0.62}
    def test_the_predicted_trace_is_the_books_number(self) -> None:
        assert FRESH_TRACE == 0.81
    def test_it_is_not_the_subtractive_prediction(self) -> None:
        assert FRESH_TRACE != 0.80
    def test_the_northern_claim_is_contradicted(self) -> None:
        verdict = check(self.NORTH, self.SOUTH_EAST)
        assert verdict.predicted == 0.81
        assert verdict.measured == 0.0
        assert verdict.gap == pytest.approx(1.0)
        assert verdict.contradicted
    def test_the_verdict_reads_as_the_book_describes_it(self) -> None:
        assert "CONTRADICTED" in str(check(self.NORTH, self.SOUTH_EAST))
        assert "100%" in str(check(self.NORTH, self.SOUTH_EAST))
    def test_pursuit_re_aims_at_the_real_source(self) -> None:
        assert true_source(self.SOUTH_EAST) == (6, 6)
    def test_a_truthful_northern_claim_is_supported(self) -> None:
        assert not check(self.NORTH, {(0, 3): 0.81}).contradicted
class TestTheGapIsGradedNotBinary:
    def test_a_fully_supported_claim_scores_zero(self) -> None:
        assert check({(0, 0): 1.0}, {(0, 0): 0.81}).gap == pytest.approx(0.0)
    def test_a_partly_supported_claim_scores_in_between(self) -> None:
        assert 0.0 < check({(0, 0): 1.0}, {(0, 0): 0.4}).gap < 1.0
    def test_stronger_evidence_survives_being_exceeded(self) -> None:
        assert check({(0, 0): 1.0}, {(0, 0): 0.9}).gap == 0.0
    def test_the_ratio_matters_not_the_difference(self) -> None:
        damning = Verdict(predicted=0.81, measured=0.0, cells=((0, 0),))
        faint = Verdict(predicted=0.05, measured=0.0, cells=((0, 0),))
        assert damning.gap == faint.gap == 1.0
        assert damning.predicted > faint.predicted
    def test_a_claim_predicting_nothing_is_never_a_contradiction(self) -> None:
        assert Verdict(predicted=0.0, measured=0.0, cells=()).gap == 0.0
        assert not Verdict(predicted=0.0, measured=0.0, cells=()).contradicted
    def test_the_threshold_sits_between_noise_and_the_books_case(self) -> None:
        assert 0.0 < CONTRADICTION < 1.0
class TestARegionalClaim:
    def test_the_strongest_cell_answers_for_the_region(self) -> None:
        claim = {(0, 0): 1.0, (0, 1): 1.0, (0, 2): 1.0}
        assert not check(claim, {(0, 2): 0.81}).contradicted
    def test_a_region_with_no_trace_anywhere_is_still_caught(self) -> None:
        claim = {(0, 0): 1.0, (0, 1): 1.0, (0, 2): 1.0}
        assert check(claim, {(6, 6): 0.9}).contradicted
    def test_the_cells_checked_are_recorded(self) -> None:
        verdict = check({(1, 1): 1.0, (0, 0): 1.0}, {})
        assert verdict.cells == ((0, 0), (1, 1))
class TestTheTrailCannotLie:
    def test_what_is_exposed_is_the_claim_not_the_field(self) -> None:
        verdict = check({(0, 3): 1.0}, {(6, 6): 0.9})
        assert verdict.contradicted
        assert verdict.measured == 0.0
    def test_an_empty_field_convicts_any_claim(self) -> None:
        assert check({(0, 0): 1.0}, {}).contradicted
    def test_no_source_when_nothing_has_been_smelled(self) -> None:
        assert true_source({}) is None
    def test_the_source_is_stable_under_ties(self) -> None:
        assert true_source({(4, 4): 0.5, (1, 1): 0.5}) == (1, 1)
    def test_the_check_is_symmetric(self) -> None:
        assert check({(2, 2): 1.0}, {(2, 2): 0.81}).contradicted is False
        assert check({(2, 2): 1.0}, {(5, 5): 0.81}).contradicted is True
class TestAdaptiveReliability:
    LIE = check({(0, 3): 1.0}, {(6, 6): 0.9})
    TRUTH = check({(6, 6): 1.0}, {(6, 6): 0.81})
    def test_an_unheard_opponent_starts_neither_trusted_nor_dismissed(self) -> None:
        assert Credibility().reliability == 0.5
        assert not Credibility().discredited
    def test_a_contradiction_lowers_it(self) -> None:
        credibility = Credibility()
        before = credibility.reliability
        assert credibility.observe(self.LIE) < before
        assert credibility.discredited
    def test_it_collapses_fast(self) -> None:
        credibility = Credibility()
        assert round(credibility.observe(self.LIE), 3) == 0.175
        assert round(credibility.observe(self.LIE), 3) == 0.061
        assert credibility.observe(self.LIE) == MIN_RELIABILITY
    def test_support_raises_it(self) -> None:
        credibility = Credibility()
        assert credibility.observe(self.TRUTH) > 0.5
    def test_recovery_is_slower_than_the_fall(self) -> None:
        alternating = Credibility()
        for _ in range(6):
            alternating.observe(self.LIE)
            alternating.observe(self.TRUTH)
        assert alternating.reliability < 0.5
    def test_a_consistently_honest_opponent_earns_trust(self) -> None:
        credibility = Credibility()
        for _ in range(20):
            credibility.observe(self.TRUTH)
        assert credibility.reliability > 0.9
        assert not credibility.discredited
    def test_trust_never_reaches_certainty(self) -> None:
        credibility = Credibility()
        for _ in range(200):
            credibility.observe(self.TRUTH)
        assert credibility.reliability <= MAX_TRUST < 1.0
    def test_a_proven_liar_is_still_heard_faintly(self) -> None:
        credibility = Credibility()
        for _ in range(50):
            credibility.observe(self.LIE)
        assert credibility.reliability == MIN_RELIABILITY > 0.0
    def test_a_liar_can_climb_back(self) -> None:
        credibility = Credibility()
        credibility.observe(self.LIE)
        credibility.observe(self.LIE)
        floor = credibility.reliability
        for _ in range(10):
            credibility.observe(self.TRUTH)
        assert credibility.reliability > floor
        assert credibility.discredited
    def test_the_counts_are_recorded_for_the_audit(self) -> None:
        credibility = Credibility()
        credibility.observe(self.LIE)
        credibility.observe(self.TRUTH)
        assert (credibility.lies, credibility.supported) == (1, 1)
        assert "1 contradicted" in str(credibility)
    def test_it_feeds_the_inference_layer_directly(self) -> None:
        from cop_agent.domain.belief import Belief
        from cop_agent.domain.board import BoardState
        from cop_agent.domain.inference import update
        board = BoardState(cop=(0, 0), thief=(6, 6), grid_size=7)
        credibility = Credibility()
        credibility.observe(self.LIE)
        credibility.observe(self.LIE)
        belief = Belief.uniform(board)
        update(belief, {(6, 6): 0.9}, claim={(0, 0): 1.0}, reliability=credibility.reliability)
        assert belief.most_likely() == (6, 6), "a discredited hint must not steer us"
