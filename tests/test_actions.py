"""Tests for turn actions and the move-or-place exclusivity rule."""

import dataclasses
import typing

import pytest

from cop_agent.domain.actions import (
    Action,
    IllegalActionError,
    MoveAction,
    PlaceBarrier,
    apply_action,
    place_barrier,
)
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.domain.rules import IllegalMoveError

AXES = AxisConvention()


def make(**kw: object) -> BoardState:
    base: dict[str, object] = {"grid_size": 7, "cop": (0, 0), "thief": (3, 3)}
    base.update(kw)
    return BoardState(**base)  # type: ignore[arg-type]


class TestExclusivityByConstruction:
    def test_an_action_is_one_variant_or_the_other(self) -> None:
        """There is no representable value meaning 'move and place'."""
        assert set(typing.get_args(Action)) == {MoveAction, PlaceBarrier}

    def test_moving_never_places_a_barrier(self) -> None:
        after = apply_action(make(), "cop", MoveAction("S"), AXES)
        assert after.barriers == frozenset()
        assert after.barriers_used == 0

    def test_placing_never_moves_the_cop(self) -> None:
        """Forfeiting movement is the cost that makes placement a decision."""
        before = make(cop=(2, 2))
        after = apply_action(before, "cop", PlaceBarrier((2, 3)), AXES)
        assert after.cop == before.cop
        assert after.barriers == frozenset({(2, 3)})

    def test_placing_never_moves_the_thief_either(self) -> None:
        before = make()
        after = apply_action(before, "cop", PlaceBarrier((1, 1)), AXES)
        assert after.thief == before.thief


class TestActionTypes:
    def test_actions_are_frozen(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            MoveAction("N").move = "S"  # type: ignore[misc]
        with pytest.raises(dataclasses.FrozenInstanceError):
            PlaceBarrier((1, 1)).at = (2, 2)  # type: ignore[misc]

    def test_actions_are_comparable(self) -> None:
        assert MoveAction("N") == MoveAction("N")
        assert PlaceBarrier((1, 1)) == PlaceBarrier((1, 1))

    def test_variants_are_never_equal(self) -> None:
        # Compared as objects: the two types do not overlap, which mypy
        # rejects as a static comparison but is worth pinning at runtime.
        move: object = MoveAction("N")
        place: object = PlaceBarrier((1, 1))
        assert move != place


class TestOnlyTheCopPlaces:
    def test_thief_cannot_place_a_barrier(self) -> None:
        with pytest.raises(IllegalActionError, match="only the cop"):
            apply_action(make(), "thief", PlaceBarrier((3, 4)), AXES)

    def test_thief_may_still_move(self) -> None:
        assert apply_action(make(), "thief", MoveAction("N"), AXES).thief == (2, 3)


class TestPlaceBarrier:
    def test_returns_a_new_state(self) -> None:
        before = make()
        after = place_barrier(before, (1, 1), AXES)
        assert after is not before
        assert before.barriers == frozenset()

    def test_rejects_an_off_board_cell(self) -> None:
        with pytest.raises(IllegalActionError, match="off a 7 board"):
            place_barrier(make(), (9, 9), AXES)

    def test_adds_to_existing_barriers(self) -> None:
        state = make(barriers=frozenset({(1, 1)}))
        assert place_barrier(state, (2, 2), AXES).barriers == frozenset({(1, 1), (2, 2)})

    def test_preserves_step_and_positions(self) -> None:
        before = make(step=5)
        after = place_barrier(before, (1, 1), AXES)
        assert (after.step, after.cop, after.thief) == (5, before.cop, before.thief)


class TestApplyActionDispatch:
    def test_illegal_move_still_raises_from_the_move_path(self) -> None:
        with pytest.raises(IllegalMoveError):
            apply_action(make(cop=(0, 0)), "cop", MoveAction("N"), AXES)

    def test_honours_the_negotiated_convention(self) -> None:
        flipped = AxisConvention(origin_corner="bottom-left")
        assert apply_action(make(), "thief", MoveAction("N"), flipped).thief == (4, 3)


class TestExhaustiveness:
    def test_dispatch_is_statically_exhaustive(self) -> None:
        """`assert_never` makes mypy fail if a variant is added unhandled."""
        foreign = typing.cast(Action, object())
        with pytest.raises(AssertionError):
            apply_action(make(), "cop", foreign, AXES)
