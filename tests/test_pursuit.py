"""Tests for re-aiming pursuit after a detected lie (#61)."""

import logging

import pytest

from cop_agent.domain.belief import Belief
from cop_agent.domain.board import BoardState
from cop_agent.domain.credibility import MIN_RELIABILITY, Credibility
from cop_agent.strategy.pursuit import observe, reaim, target

BOARD = BoardState(cop=(0, 0), thief=(6, 6), grid_size=7)
SOUTH_EAST = {(6, 6): 0.9, (6, 5): 0.62, (5, 6): 0.62}
NORTH_CLAIM = {(0, 3): 1.0}


def fresh() -> tuple[Belief, Credibility]:
    return Belief.uniform(BOARD), Credibility()


class TestTheBooksWorkedExample:
    """PDF p. 47: lower the trust, re-weight the matrix, re-aim pursuit."""

    def test_all_three_happen_in_one_call(self) -> None:
        belief, credibility = fresh()
        aim, verdict = reaim(belief, credibility, SOUTH_EAST, claim=NORTH_CLAIM)
        assert verdict is not None and verdict.contradicted
        assert credibility.reliability < 0.5
        assert belief.at((6, 6)) > belief.at((0, 3))
        assert aim == (6, 6)

    def test_it_aims_at_the_source_not_the_claim(self) -> None:
        belief, credibility = fresh()
        aim, _ = reaim(belief, credibility, SOUTH_EAST, claim=NORTH_CLAIM)
        assert aim != (0, 3)

    def test_and_not_at_the_negation_of_the_claim_either(self) -> None:
        """A lie says the claim is false; it does not say the opposite is
        true. Chasing the negation is still letting the liar pick our heading.
        """
        belief, credibility = fresh()
        scattered = {(2, 5): 0.9, (2, 4): 0.62}
        aim, verdict = reaim(belief, credibility, scattered, claim={(0, 0): 1.0})
        assert verdict is not None and verdict.contradicted
        assert aim == (2, 5)
        assert aim != (6, 6), "the mirror of (0, 0) is not where the trail points"

    def test_the_lie_is_what_exposed_the_position(self) -> None:
        """The asymmetry: had the thief stayed silent, trust would be intact
        and the hint channel still worth something to them."""
        spoke, silent = fresh(), fresh()
        reaim(*spoke, SOUTH_EAST, claim=NORTH_CLAIM)
        reaim(*silent, SOUTH_EAST, claim=None)
        assert spoke[1].reliability < silent[1].reliability
        assert spoke[1].discredited and not silent[1].discredited


class TestOrdering:
    def test_trust_is_lowered_before_the_hint_is_applied(self) -> None:
        """The ordering that stops a lie landing once at full strength.

        Applying the hint first and lowering trust afterwards would let an
        opponent alternate — paying one turn of credibility for one turn of
        misdirection, indefinitely.
        """
        belief, credibility = fresh()
        reaim(belief, credibility, SOUTH_EAST, claim=NORTH_CLAIM)
        cheated = Belief.uniform(BOARD)
        from cop_agent.domain.inference import update

        update(cheated, SOUTH_EAST, claim=NORTH_CLAIM, reliability=0.5)
        assert belief.at((0, 3)) < cheated.at((0, 3))

    def test_a_repeated_liar_loses_the_channel_entirely(self) -> None:
        belief, credibility = fresh()
        for _ in range(4):
            reaim(belief, credibility, SOUTH_EAST, claim=NORTH_CLAIM)
        assert credibility.reliability == MIN_RELIABILITY
        assert belief.most_likely() == (6, 6)

    def test_an_honest_opponent_keeps_steering_us(self) -> None:
        belief, credibility = fresh()
        for _ in range(3):
            reaim(belief, credibility, SOUTH_EAST, claim={(6, 6): 1.0})
        assert not credibility.discredited
        assert credibility.reliability > 0.5
        assert belief.most_likely() == (6, 6)


class TestSilentTurns:
    def test_no_claim_yields_no_verdict(self) -> None:
        belief, credibility = fresh()
        aim, verdict = reaim(belief, credibility, SOUTH_EAST, claim=None)
        assert verdict is None
        assert aim == (6, 6)

    def test_belief_still_updates_from_the_trail(self) -> None:
        """The trail speaks whether or not the thief does."""
        belief, credibility = fresh()
        observe(belief, credibility, SOUTH_EAST)
        assert belief.at((6, 6)) > belief.at((0, 0))

    def test_silence_costs_the_opponent_no_credibility(self) -> None:
        belief, credibility = fresh()
        reaim(belief, credibility, SOUTH_EAST, claim=None)
        assert credibility.reliability == 0.5


class TestTheTarget:
    def test_belief_leads_once_it_has_concentrated(self) -> None:
        belief, credibility = fresh()
        reaim(belief, credibility, {(1, 1): 0.9})
        assert target(belief, {(1, 1): 0.9}) == belief.most_likely()

    def test_the_trail_answers_before_belief_has_anything(self) -> None:
        """A uniform prior's argmax is (0, 0) whatever the board says — the
        opening turns would send the cop to a corner on principle."""
        belief = Belief.uniform(BOARD)
        assert belief.concentration() == pytest.approx(0.0)
        assert belief.most_likely() == (0, 0)
        assert target(belief, SOUTH_EAST) == (6, 6)

    def test_nothing_to_aim_at_yields_none(self) -> None:
        assert target(Belief.uniform(BOARD), {}) is None

    def test_it_is_stable_across_calls(self) -> None:
        belief, credibility = fresh()
        reaim(belief, credibility, SOUTH_EAST, claim=NORTH_CLAIM)
        assert target(belief, SOUTH_EAST) == target(belief, SOUTH_EAST)


class TestItIsLogged:
    def test_the_re_aim_is_recorded(self, caplog: pytest.LogCaptureFixture) -> None:
        belief, credibility = fresh()
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.pursuit"):
            reaim(belief, credibility, SOUTH_EAST, claim=NORTH_CLAIM)
        assert "CONTRADICTED" in caplog.text
        assert "re-aiming at (6, 6)" in caplog.text

    def test_a_supported_claim_is_not_reported_as_a_lie(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        belief, credibility = fresh()
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.pursuit"):
            reaim(belief, credibility, SOUTH_EAST, claim={(6, 6): 1.0})
        assert "re-aiming" not in caplog.text
