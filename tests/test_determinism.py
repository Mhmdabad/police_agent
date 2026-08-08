"""Tests for replay determinism (#48).

The acceptance criterion is *across processes and runs*, and the two are not
the same claim. Within one process a policy can be perfectly reproducible and
still differ from the peer replaying it, because Python randomises string and
tuple hashing per process: anything reading a ``set`` or ``dict`` in iteration
order is stable for a run and unstable for a match.

That risk is real here rather than theoretical. ``placement_range`` returns a
``frozenset``, and the cop reads it twice — once to find a winning placement,
where the *first* match is returned, and once to rank candidates. Both are
sorted first, and this is where that is enforced.
"""

import logging
import os
import subprocess
import sys

import pytest

from cop_agent.domain.actions import MoveAction, PlaceBarrier, placement_range
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.strategy.barriers import candidates, rank_placements
from cop_agent.strategy.police_brain import PoliceBrain

AXES = AxisConvention()

DECIDE = """
import json
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.strategy.police_brain import PoliceBrain

axes = AxisConvention()
brain = PoliceBrain(axes=axes, seed=7)
walls = frozenset({(1, 1), (2, 2), (3, 1), (0, 4), (4, 4), (5, 2)})
actions = []
for step in range(6):
    state = BoardState(
        cop=(2, min(6, step)), thief=(5, 5), grid_size=7, barriers=walls, step=step
    )
    actions.append(repr(brain.decide(state).action))
print(json.dumps(actions))
"""


def run_with_hash_seed(seed: str) -> str:
    env = {**os.environ, "PYTHONHASHSEED": seed}
    result = subprocess.run(
        [sys.executable, "-c", DECIDE], env=env, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def make(**kw: object) -> BoardState:
    cop = kw.get("cop", (0, 0))
    thief = kw.get("thief", (3, 3))
    barriers = kw.get("barriers", frozenset())
    step = kw.get("step", 0)
    assert isinstance(cop, tuple) and isinstance(thief, tuple)
    assert isinstance(barriers, frozenset | set) and isinstance(step, int)
    return BoardState(cop=cop, thief=thief, grid_size=7, barriers=frozenset(barriers), step=step)


class TestAcrossProcesses:
    def test_hash_randomisation_does_not_change_the_actions(self) -> None:
        """#48's acceptance criterion, tested rather than asserted.

        If either read of ``placement_range`` lost its sort, these would
        disagree — and only between peers, never within our own run, which is
        the failure that survives to a match and gets blamed on the network.
        """
        results = {run_with_hash_seed(seed) for seed in ("0", "1", "42", "12345")}
        assert len(results) == 1, f"hash seed changed the decisions: {results}"

    def test_the_subprocess_actually_decided_something(self) -> None:
        assert (
            run_with_hash_seed("0").count("Action") + run_with_hash_seed("0").count("Barrier") == 6
        )


class TestTheFrozensetReads:
    def test_candidates_are_sorted(self) -> None:
        """The winning-placement search returns the first match, so with two
        available wins the choice would otherwise be iteration order — and
        both peers would claim a different capture cell, both truthfully."""
        state = make(cop=(3, 3), thief=(5, 5))
        assert candidates(state, AXES) == sorted(placement_range(state, AXES))

    def test_the_ranking_is_stable_under_reconstruction(self) -> None:
        state = make(cop=(3, 3), thief=(5, 5))
        rebuilt = make(cop=(3, 3), thief=(5, 5), barriers=set())
        assert [s.at for s in rank_placements(state, AXES, (5, 5))] == [
            s.at for s in rank_placements(rebuilt, AXES, (5, 5))
        ]


class TestAcrossRuns:
    def test_the_brain_carries_no_history(self) -> None:
        """Unlike the thief, the cop's decision is a pure function of the
        state: the barrier count it budgets against comes from the board, not
        from memory. A fresh brain per turn is therefore a valid replay."""
        walls = frozenset({(1, 1), (2, 2), (3, 1)})
        states = [
            make(cop=(2, min(6, step)), thief=(5, 5), barriers=walls, step=step)
            for step in range(8)
        ]
        continuous = PoliceBrain(axes=AXES, seed=3)
        together = [continuous.decide(state).action for state in states]
        apart = [PoliceBrain(axes=AXES, seed=3).decide(state).action for state in states]
        assert together == apart

    def test_a_whole_match_replays_identically(self) -> None:
        walls = frozenset({(1, 1), (2, 2), (3, 1)})
        states = [
            make(cop=(2, min(6, step)), thief=(5, 5), barriers=walls, step=step)
            for step in range(8)
        ]
        first = [PoliceBrain(axes=AXES, seed=3).decide(s).action for s in states]
        second = [PoliceBrain(axes=AXES, seed=3).decide(s).action for s in states]
        assert len(first) == 8
        assert first == second

    def test_placements_replay_too_not_only_moves(self) -> None:
        """The cop has two kinds of turn and both must reproduce."""
        walls = frozenset({(0, 2), (1, 2), (3, 2), (4, 2), (5, 2), (6, 2)})
        state = make(cop=(2, 1), thief=(2, 5), barriers=walls)
        first = PoliceBrain(axes=AXES, seed=3).decide(state).action
        assert isinstance(first, PlaceBarrier)
        assert PoliceBrain(axes=AXES, seed=3).decide(state).action == first


class TestTheSeedIsRecoverable:
    def test_it_is_on_every_turn_not_once_at_startup(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.police_brain"):
            brain = PoliceBrain(axes=AXES, seed=4242)
            brain.decide(make(step=0))
            brain.decide(make(step=1))
        assert caplog.text.count("seed=4242") == 2

    def test_the_default_is_recorded_too(self, caplog: pytest.LogCaptureFixture) -> None:
        """Zero is a seed. An unlogged default is the one nobody reproduces."""
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.police_brain"):
            PoliceBrain(axes=AXES).decide(make())
        assert "seed=0" in caplog.text

    def test_it_survives_on_the_object(self) -> None:
        assert PoliceBrain(axes=AXES, seed=99).seed == 99


class TestNoHiddenRandomness:
    def test_the_policy_does_not_draw_from_the_rng_at_all(self) -> None:
        """Ties break by MOVES order and by position, so the stream should be
        untouched. If a later change starts drawing, this fails and the seed
        becomes load bearing rather than decorative."""
        brain = PoliceBrain(axes=AXES, seed=11)
        before = brain.rng.getstate()
        for step in range(5):
            brain.decide(make(cop=(0, step), step=step))
        assert brain.rng.getstate() == before

    def test_the_global_rng_is_never_used(self) -> None:
        import random

        random.seed(1)
        first = PoliceBrain(axes=AXES, seed=0).decide(make(cop=(2, 2))).action
        random.seed(999999)
        second = PoliceBrain(axes=AXES, seed=0).decide(make(cop=(2, 2))).action
        assert first == second
        assert isinstance(first, MoveAction)

    def test_config_changes_the_action_and_is_part_of_the_claim(self) -> None:
        """State *plus config*, as #48 phrases it: a different quota is a
        different game, and may legitimately produce a different action."""
        walls = frozenset({(0, 2), (1, 2), (3, 2), (4, 2), (5, 2), (6, 2)})
        state = make(cop=(2, 1), thief=(2, 5), barriers=walls)
        assert isinstance(PoliceBrain(axes=AXES).decide(state).action, PlaceBarrier)
        spent = PoliceBrain(axes=AXES, max_barriers=6)
        assert isinstance(spent.decide(state).action, MoveAction)
