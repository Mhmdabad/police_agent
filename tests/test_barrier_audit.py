"""Barriers are irreversible, so their declarations get re-derived."""

import pytest

from cop_agent.domain.barrier_audit import declared, rebuild_states, replay
from cop_agent.infra.ceremony import Reveal

WHEN = "2026-08-04T09:00:00+00:00"


def opened(step: int, barrier: list[int] | None = None, move: str = "N") -> Reveal:
    return Reveal(
        step=step,
        sender="police",
        move=move,
        intent="truth",
        hint=f"step {step}",
        timestamp=WHEN,
        barrier_placed=barrier,
    )


def series(*barriers: list[int] | None) -> dict[int, Reveal]:
    return {step: opened(step, cell) for step, cell in enumerate(barriers, start=1)}


class TestReadingTheDeclarations:
    def test_it_lists_every_declared_barrier_oldest_first(self) -> None:
        history = replay(series([1, 1], None, [2, 2]))
        assert history.placements == ((1, (1, 1)), (3, (2, 2)))

    def test_turns_without_a_barrier_contribute_nothing(self) -> None:
        assert declared(series(None, None)) == ()

    def test_wire_cells_become_positions(self) -> None:
        """A list would compare unequal to every position in a barrier set."""
        assert declared(series([1, 1]))[0][1] == (1, 1)

    def test_a_clean_series_is_sound(self) -> None:
        history = replay(series([0, 0], [0, 1], [0, 2]))
        assert history.sound
        assert "3 barriers declared, all consistent" in str(history)


class TestHistoriesThatCannotHaveHappened:
    def test_the_same_cell_sealed_twice(self) -> None:
        """Every step verifies individually and the sequence is still impossible."""
        history = replay(series([1, 1], [1, 1]))
        assert not history.sound
        assert "already sealed" in history.problems[0]

    def test_a_barrier_on_a_cell_that_started_sealed(self) -> None:
        history = replay(series([1, 1]), start=frozenset({(1, 1)}))
        assert "already sealed" in history.problems[0]

    def test_the_quota_exceeded_across_the_series(self) -> None:
        """No single step is wrong; the series is."""
        history = replay(series([0, 0], [0, 1], [0, 2]), quota=2)
        assert "exceeds the agreed quota" in history.problems[0]

    def test_a_barrier_off_the_board(self) -> None:
        history = replay(series([9, 9]), grid_size=6)
        assert "off a 6 board" in history.problems[0]

    def test_every_problem_is_collected(self) -> None:
        """An accusation they can only see half of is one contested twice."""
        history = replay(series([1, 1], [1, 1], [9, 9]), quota=1, grid_size=6)
        assert len(history.problems) >= 3
        assert "3 barriers declared" in str(history)

    def test_the_board_size_check_is_optional(self) -> None:
        """A caller without an agreed grid size still gets the other checks."""
        assert replay(series([9, 9])).sound


class TestRebuildingTheBoardEachStepWasSealedAgainst:
    def trajectory(self, steps: int) -> dict[int, tuple[tuple[int, int], tuple[int, int]]]:
        return {step: ((0, step - 1), (5, 5)) for step in range(1, steps + 1)}

    def test_it_yields_one_state_per_step(self) -> None:
        states = rebuild_states(series(None, None), self.trajectory(2), grid_size=6)
        assert sorted(states) == [1, 2]
        assert states[2].cop == (0, 1)

    def test_barriers_accumulate_as_the_series_runs(self) -> None:
        states = rebuild_states(series([1, 1], [2, 2], None), self.trajectory(3), grid_size=6)
        assert states[2].barriers == frozenset({(1, 1)})
        assert states[3].barriers == frozenset({(1, 1), (2, 2)})

    def test_a_step_is_sealed_against_the_board_before_its_own_placement(self) -> None:
        """The agent had not laid that barrier yet when it chose to.

        Off by one here re-derives every barrier-placing step wrongly and
        reports a clean cop as a forger.
        """
        states = rebuild_states(series([1, 1]), self.trajectory(1), grid_size=6)
        assert states[1].barriers == frozenset()

    def test_a_pre_existing_barrier_set_is_carried_in(self) -> None:
        states = rebuild_states(
            series(None), self.trajectory(1), grid_size=6, start=frozenset({(4, 4)})
        )
        assert states[1].barriers == frozenset({(4, 4)})

    def test_a_step_with_no_known_trajectory_is_skipped(self) -> None:
        """Better a step the ceremony audit reports as unrebuildable.

        Inventing a position would produce a digest mismatch and accuse an
        honest opponent of forgery.
        """
        states = rebuild_states(series(None, None), self.trajectory(1), grid_size=6)
        assert sorted(states) == [1]

    def test_the_rebuilt_state_is_a_real_board(self) -> None:
        """Construction validates, so an impossible reconstruction raises here."""
        with pytest.raises(ValueError, match="off a 6 board"):
            rebuild_states(series(None), {1: ((9, 9), (5, 5))}, grid_size=6)
