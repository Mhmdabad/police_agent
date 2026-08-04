"""Tests for the cop's brain and its selection from config."""

import random
import tomllib
from pathlib import Path
from typing import Any

import pytest

from cop_agent.domain.actions import (
    IllegalActionError,
    MoveAction,
    PlaceBarrier,
    place_barrier,
    placement_range,
)
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import MOVES, Agent, BoardState, Move
from cop_agent.domain.outcome import is_capture_by_overlap
from cop_agent.domain.rules import legal_moves, target_of
from cop_agent.domain.search import reachable_area
from cop_agent.strategy.barriers import winning_placement
from cop_agent.strategy.base import BrainBase, Decision, NoLegalActionError
from cop_agent.strategy.loader import DEFAULT_BRAIN, StrategyError, load_brain
from cop_agent.strategy.police_brain import PoliceBrain, manhattan
from cop_agent.strategy.tradeoff import weigh

AXES = AxisConvention()


def make(**kw: object) -> BoardState:
    base: dict[str, object] = {"grid_size": 7, "cop": (0, 0), "thief": (3, 3)}
    base.update(kw)
    return BoardState(**base)  # type: ignore[arg-type]


class TestManhattan:
    def test_matches_the_rulebook_worked_example(self) -> None:
        """Cop (2,2), target (5,5): D = 3 + 3 = 6."""
        assert manhattan((2, 2), (5, 5)) == 6

    def test_is_symmetric(self) -> None:
        assert manhattan((1, 2), (4, 6)) == manhattan((4, 6), (1, 2))

    def test_a_cell_is_zero_from_itself(self) -> None:
        assert manhattan((3, 3), (3, 3)) == 0

    def test_ignores_barriers(self) -> None:
        """Admissible: it never overestimates the true step count."""
        assert manhattan((0, 0), (0, 2)) == 2


class TestPursuit:
    def test_closes_distance_from_the_corner(self) -> None:
        brain = PoliceBrain(axes=AXES)
        move = brain.decide(make()).action
        assert isinstance(move, MoveAction)
        assert move.move in {"S", "E"}

    def test_the_rulebook_worked_example(self) -> None:
        """Cop (2,2) chasing (5,5): east or south both reduce D to 5."""
        brain = PoliceBrain(axes=AXES)
        action = brain.decide(make(cop=(2, 2), thief=(5, 5))).action
        assert isinstance(action, MoveAction)
        assert action.move in {"S", "E"}

    def test_never_increases_the_distance_when_it_chooses_to_move(self) -> None:
        """The pursuit invariant, now scoped to the turns it governs.

        Since #45 and #46 the cop also has a placement turn, so "the action is
        a move" is no longer an invariant of the policy. Where a win exists the
        assertion is stronger — the win is taken — and where the cop moves the
        old invariant holds unchanged.
        """
        brain = PoliceBrain(axes=AXES)
        placements = 0
        for row in range(7):
            for col in range(7):
                state = make(cop=(row, col), thief=(6, 6))
                if is_capture_by_overlap(state):
                    continue  # already won; decide() is not defined for a finished position
                before = manhattan(state.cop, state.thief)
                action = brain.decide(state).action
                win = winning_placement(state, AXES)
                if win is not None:
                    assert action == PlaceBarrier(win)
                    placements += 1
                    continue
                assert isinstance(action, MoveAction)
                after = manhattan(target_of(state.cop, action.move, AXES), state.thief)
                assert after <= before
        assert placements > 0, "the sweep never reached a winning position"

    def test_an_explicit_target_overrides_the_thief_position(self) -> None:
        """Once a belief map exists it supplies the target instead."""
        brain = PoliceBrain(axes=AXES)
        action = brain.decide(make(cop=(3, 3), thief=(0, 0)), target=(6, 3)).action
        assert isinstance(action, MoveAction)
        assert action.move == "S"

    def test_a_walled_in_cop_stays(self) -> None:
        walls = frozenset({(2, 3), (4, 3), (3, 2), (3, 4)})
        action = PoliceBrain(axes=AXES).decide(make(cop=(3, 3), barriers=walls)).action
        assert action == MoveAction("STAY")

    def test_honours_the_negotiated_convention(self) -> None:
        flipped = AxisConvention(origin_corner="bottom-left")
        brain = PoliceBrain(axes=flipped)
        action = brain.decide(make(cop=(3, 3), thief=(0, 3))).action
        assert isinstance(action, MoveAction)
        assert action.move == "S"


class TestLegalityGuard:
    def test_the_policy_never_returns_an_illegal_move(self) -> None:
        brain = PoliceBrain(axes=AXES)
        walls = frozenset({(1, 1), (2, 2), (3, 3), (4, 4)})
        for row in range(7):
            for col in range(7):
                state = make(cop=(row, col), thief=(6, 6), barriers=walls)
                if state.is_barrier(state.cop):
                    continue
                action = brain.decide(state).action
                if isinstance(action, PlaceBarrier):
                    assert action.at in placement_range(state, AXES)
                    assert not state.is_barrier(action.at)
                else:
                    assert action.move in brain.options(state)

    def test_a_rogue_subclass_is_caught(self) -> None:
        """Defence in depth: the guard runs on whatever a subclass produced."""

        class Rogue(PoliceBrain):
            def _pick_move(self, state: BoardState, **context: object) -> Move:
                return "N"

        with pytest.raises(NoLegalActionError, match="not among"):
            Rogue(axes=AXES).decide(make(cop=(0, 0)))

    def test_the_base_default_relocates(self) -> None:
        """PoliceBrain overrides _decide_move to weigh barriers, so the base
        class's own default - relocate, no alternative - is only reachable
        through a role that has none. It is still the contract a thief brain
        inherits, so it is exercised here rather than left unrun."""

        class MoveOnly(BrainBase):
            @property
            def role(self) -> Agent:
                return "cop"

            def _pick_move(self, state: BoardState, **context: object) -> Move:
                return "STAY"

        assert MoveOnly(axes=AXES).decide(make()).action == MoveAction("STAY")

    def test_the_guard_cannot_be_bypassed_by_overriding_pick_move(self) -> None:
        """`decide` is the entry point; subclasses override the hooks."""
        assert "_guard" in BrainBase.decide.__code__.co_names

    def test_a_sealed_cop_has_nothing_legal(self) -> None:
        """Sealed in place with every neighbour blocked: no move exists."""
        walls = frozenset({(3, 3), (2, 3), (4, 3), (3, 2), (3, 4)})
        with pytest.raises(NoLegalActionError, match="no legal move"):
            PoliceBrain(axes=AXES).decide(make(cop=(3, 3), barriers=walls))

    def test_the_guard_reports_an_empty_option_set(self) -> None:
        """A subclass that acts anyway is caught by the guard, not the policy."""

        class Stubborn(PoliceBrain):
            def _pick_move(self, state: BoardState, **context: object) -> Move:
                return "N"

        walls = frozenset({(3, 3), (2, 3), (4, 3), (3, 2), (3, 4)})
        with pytest.raises(NoLegalActionError, match="has no legal move"):
            Stubborn(axes=AXES).decide(make(cop=(3, 3), barriers=walls))

    def test_a_legal_placement_passes(self) -> None:
        PoliceBrain(axes=AXES)._guard(make(cop=(0, 0)), PlaceBarrier((1, 0)))

    def test_a_placement_out_of_reach_is_refused(self) -> None:
        """This used to pass. The guard checked moves and let every barrier
        through on the grounds that placement legality belonged to the domain
        layer — which validates it after it has gone out on the wire, where
        the thief rejects it and we take a technical loss."""
        with pytest.raises(NoLegalActionError, match="illegal barrier"):
            PoliceBrain(axes=AXES)._guard(make(cop=(0, 0)), PlaceBarrier((5, 5)))

    def test_a_placement_off_the_board_is_refused(self) -> None:
        with pytest.raises(NoLegalActionError, match="illegal barrier"):
            PoliceBrain(axes=AXES)._guard(make(cop=(0, 0)), PlaceBarrier((-1, 0)))

    def test_a_placement_on_an_existing_barrier_is_refused(self) -> None:
        """Barriers are permanent; sealing one twice spends a barrier on
        nothing and is not a legal action."""
        state = make(cop=(0, 0), barriers=frozenset({(1, 0)}))
        with pytest.raises(NoLegalActionError, match="illegal barrier"):
            PoliceBrain(axes=AXES)._guard(state, PlaceBarrier((1, 0)))

    def test_a_placement_beyond_the_quota_is_refused(self) -> None:
        walls = frozenset({(6, col) for col in range(7)})
        state = make(cop=(0, 0), barriers=walls)
        brain = PoliceBrain(axes=AXES, max_barriers=7)
        with pytest.raises(NoLegalActionError, match="illegal barrier"):
            brain._guard(state, PlaceBarrier((1, 0)))

    def test_the_guard_never_lets_an_illegal_action_through(self) -> None:
        """#47's acceptance criterion: a property, over random boards, for
        both kinds of turn."""
        rng = random.Random(47)
        cells = [(row, col) for row in range(7) for col in range(7)]
        brain = PoliceBrain(axes=AXES)
        rejected_moves = rejected_placements = 0
        for _ in range(200):
            walls = frozenset(rng.sample(cells, rng.randint(0, 20)))
            free = [cell for cell in cells if cell not in walls]
            state = make(cop=rng.choice(free), thief=rng.choice(free), barriers=walls)
            legal = legal_moves(state, "cop", AXES)
            reach = placement_range(state, AXES)
            for move in MOVES:
                if move in legal:
                    brain._guard(state, MoveAction(move))
                else:
                    rejected_moves += 1
                    with pytest.raises(NoLegalActionError):
                        brain._guard(state, MoveAction(move))
            affordable = state.barriers_used < brain.max_barriers
            for cell in cells:
                permitted = affordable and cell in reach and not state.is_barrier(cell)
                if permitted:
                    brain._guard(state, PlaceBarrier(cell))
                else:
                    rejected_placements += 1
                    with pytest.raises(NoLegalActionError):
                        brain._guard(state, PlaceBarrier(cell))
        assert rejected_moves > 0 and rejected_placements > 0

    def test_the_guard_agrees_with_the_domain_by_construction(self) -> None:
        """It attempts the placement rather than restating the rules, so the
        two cannot drift into disagreeing."""
        state = make(cop=(3, 3), barriers=frozenset({(3, 4)}))
        for cell in ((3, 4), (0, 0), (3, 3), (2, 3)):
            try:
                place_barrier(state, cell, AXES)
            except IllegalActionError:
                with pytest.raises(NoLegalActionError):
                    PoliceBrain(axes=AXES)._guard(state, PlaceBarrier(cell))
            else:
                PoliceBrain(axes=AXES)._guard(state, PlaceBarrier(cell))


class TestDeterminism:
    def test_same_state_and_seed_yields_the_same_action(self) -> None:
        state = make(cop=(2, 2), thief=(5, 5))
        first = PoliceBrain(axes=AXES, seed=7).decide(state).action
        second = PoliceBrain(axes=AXES, seed=7).decide(state).action
        assert first == second

    def test_the_seed_is_recorded_on_the_brain(self) -> None:
        """A match cannot be replayed if the seed is not known."""
        assert PoliceBrain(axes=AXES, seed=99).seed == 99

    def test_randomness_is_seeded_not_global(self) -> None:
        a = PoliceBrain(axes=AXES, seed=1).rng.random()
        b = PoliceBrain(axes=AXES, seed=1).rng.random()
        assert a == b

    def test_different_seeds_give_different_streams(self) -> None:
        a = PoliceBrain(axes=AXES, seed=1).rng.random()
        b = PoliceBrain(axes=AXES, seed=2).rng.random()
        assert a != b


class TestDecision:
    def test_carries_an_action(self) -> None:
        assert isinstance(PoliceBrain(axes=AXES).decide(make()), Decision)

    def test_defaults_to_a_truthful_intent(self) -> None:
        """Intent is declared before sending; deception is opt-in."""
        assert PoliceBrain(axes=AXES).decide(make()).intent == "truth"


class TestLoader:
    def test_an_absent_section_loads_the_shipped_brain(self) -> None:
        assert isinstance(load_brain(None), PoliceBrain)

    def test_an_empty_section_loads_the_shipped_brain(self) -> None:
        assert isinstance(load_brain({}), PoliceBrain)

    def test_the_default_reference_resolves(self) -> None:
        assert isinstance(load_brain({"police_class": DEFAULT_BRAIN}), PoliceBrain)

    def test_a_custom_brain_is_loaded(self) -> None:
        spec = "cop_agent.strategy.police_brain:PoliceBrain"
        assert isinstance(load_brain({"police_class": spec}), BrainBase)

    def test_a_malformed_reference_is_refused(self) -> None:
        with pytest.raises(StrategyError, match="package.module:Class"):
            load_brain({"police_class": "not_a_reference"})

    def test_an_unimportable_module_is_refused(self) -> None:
        with pytest.raises(StrategyError, match="cannot import"):
            load_brain({"police_class": "no.such.module:Brain"})

    def test_a_missing_class_is_refused(self) -> None:
        with pytest.raises(StrategyError, match="has no"):
            load_brain({"police_class": "cop_agent.strategy.police_brain:Missing"})

    def test_a_non_brain_is_refused(self) -> None:
        """Loading anything callable would defer the failure to move one."""
        with pytest.raises(StrategyError, match="does not subclass"):
            load_brain({"police_class": "cop_agent.strategy.police_brain:manhattan"})

    def test_the_axis_convention_is_threaded_through(self) -> None:
        flipped = AxisConvention(origin_corner="bottom-right")
        assert load_brain({}, axes=flipped).axes == flipped

    def test_the_seed_is_threaded_through(self) -> None:
        assert load_brain({}, seed=42).seed == 42

    def test_the_shipped_private_config_selects_the_default(self) -> None:
        """The section is commented out, so the heuristic brain runs."""
        path = Path(__file__).parents[1] / "config/police/game.toml"
        private: dict[str, Any] = tomllib.loads(path.read_text())
        assert isinstance(load_brain(private.get("strategy")), PoliceBrain)


class TestContract:
    def test_the_role_is_the_cop(self) -> None:
        assert PoliceBrain(axes=AXES).role == "cop"

    def test_options_are_in_stable_order(self) -> None:
        """Replay determinism depends on both peers iterating identically."""
        brain = PoliceBrain(axes=AXES)
        state = make(cop=(3, 3))
        assert brain.options(state) == list(MOVES)

    def test_the_base_class_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            BrainBase()  # type: ignore[abstract]


class TestContainmentTieBreak:
    def test_distance_still_dominates(self) -> None:
        """Containment breaks ties; it does not override closing in."""
        brain = PoliceBrain(axes=AXES)
        state = make(cop=(0, 0), thief=(0, 6))
        action = brain.decide(state).action
        assert isinstance(action, MoveAction)
        assert action.move == "E"

    def test_a_tie_is_broken_not_left_to_position(self) -> None:
        """Cop (2,2) to (5,5): S and E both reach D=5, so something must choose."""
        brain = PoliceBrain(axes=AXES)
        action = brain.decide(make(cop=(2, 2), thief=(5, 5))).action
        assert isinstance(action, MoveAction)
        assert action.move in {"S", "E"}

    def test_it_prefers_shrinking_the_thiefs_reachable_area(self) -> None:
        """A step that seals a region beats one that merely closes distance."""
        walls = frozenset({(0, 2), (1, 2), (3, 2), (4, 2), (5, 2), (6, 2)})
        state = make(cop=(2, 1), thief=(2, 5), barriers=walls)
        assert PoliceBrain(axes=AXES)._pick_move(state) == "E"

    def test_but_a_barrier_on_the_corridor_beats_the_step(self) -> None:
        """The same position, once #46 lets the two be compared.

        Column 2 is walled except at (2, 2), and the cop stands at (2, 1) on
        the far side of that gap. Sealing its own cell cuts the fourteen cells
        of the left region out of the thief's world — a third of the board —
        while the best step closes one cell of distance. The cop keeps its
        route out through (2, 2), so nothing is refused.
        """
        walls = frozenset({(0, 2), (1, 2), (3, 2), (4, 2), (5, 2), (6, 2)})
        state = make(cop=(2, 1), thief=(2, 5), barriers=walls)
        assert reachable_area(state, (2, 5), AXES) == 43
        call = weigh(state, AXES, (2, 5), "E")
        assert call.placement is not None
        assert call.placement.at == (2, 1)
        assert (call.placement_value, call.move_gain) == (14, 1)
        assert call.place
        assert PoliceBrain(axes=AXES).decide(state).action == PlaceBarrier((2, 1))

    def test_edge_pressure_prefers_a_cornered_target(self) -> None:
        brain = PoliceBrain(axes=AXES)
        assert brain._edge_pressure(make(), (0, 0)) == 0
        assert brain._edge_pressure(make(), (3, 3)) == 3
        assert brain._edge_pressure(make(), (0, 3)) == 0

    def test_edge_pressure_is_symmetric_across_the_board(self) -> None:
        brain = PoliceBrain(axes=AXES)
        assert brain._edge_pressure(make(), (6, 6)) == 0
        assert brain._edge_pressure(make(), (1, 1)) == 1

    def test_the_ranking_is_total(self) -> None:
        """Two candidates never tie completely, so the choice is deterministic."""
        brain = PoliceBrain(axes=AXES)
        state = make(cop=(3, 3), thief=(3, 3))
        ranks = [brain._rank(state, move, state.thief) for move in brain.options(state)]
        assert len(set(ranks)) == len(ranks)

    def test_it_stays_deterministic_across_instances(self) -> None:
        state = make(cop=(2, 2), thief=(5, 5))
        first = PoliceBrain(axes=AXES).decide(state).action
        second = PoliceBrain(axes=AXES).decide(state).action
        assert first == second

    def test_it_never_returns_an_illegal_move(self) -> None:
        brain = PoliceBrain(axes=AXES)
        walls = frozenset({(1, 1), (2, 2), (4, 4)})
        for row in range(7):
            for col in range(7):
                state = make(cop=(row, col), thief=(6, 0), barriers=walls)
                if state.is_barrier(state.cop):
                    continue
                action = brain.decide(state).action
                if isinstance(action, PlaceBarrier):
                    assert action.at in placement_range(state, AXES)
                else:
                    assert action.move in brain.options(state)
