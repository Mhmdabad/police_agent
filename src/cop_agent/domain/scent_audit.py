"""Checking a scent field that arrived from someone who wants us wrong."""

import re
from collections.abc import Iterator, Sequence

from .actions import apply_action
from .axes import AxisConvention
from .board import Agent, BoardState, Position
from .rules import advance_turn, position_of
from .scent import CENTRE_INTENSITY, DEFAULT_FALLOFF, GRID_SIZE, Falloff, emission
from .trail import Trail

CELL = re.compile(r"^(0|[1-9][0-9]*),(0|[1-9][0-9]*)$")
"""A wire cell key, exactly as :meth:`~.trail.Trail.snapshot` renders one.

Deliberately narrower than ``int()`` would accept. ``" 1,2"``, ``"+1,2"`` and
``"01,2"`` all parse as integers and none of them is a key we would ever emit,
so accepting them would mean two peers whose fields compare unequal while both
believe they agree — the failure the pre-series lock exists to prevent.
"""


from ._scent_audit_field import (
    ScentFieldError as ScentFieldError,
)
from ._scent_audit_field import (
    StepPlay as StepPlay,
)
from ._scent_audit_field import (
    check_field as check_field,
)


def _agent(role: str) -> Agent:
    return "cop" if role == "police" else "thief"


def _walk(
    start: BoardState, axes: AxisConvention, role: str, plays: Sequence[StepPlay]
) -> Iterator[tuple[StepPlay, Position, Position]]:
    """Replay the match, yielding where each side stood after its own action."""
    mine, yours = _agent(role), _agent("thief" if role == "police" else "police")
    state = start
    for play in plays:
        try:
            state = advance_turn(state)
            state = apply_action(state, mine, play.ours, axes)
            here = position_of(state, mine)
            if play.theirs is not None:
                state = apply_action(state, yours, play.theirs, axes)
        except ValueError as exc:
            raise ScentFieldError(
                f"step {play.step}: the revealed move cannot be replayed on the agreed "
                f"board ({exc}); from here the two peers no longer share a board"
            ) from exc
        yield play, here, position_of(state, yours)


def replay(
    start: BoardState, axes: AxisConvention, role: str, plays: Sequence[StepPlay]
) -> list[tuple[Position, Position]]:
    """Where both sides stood after acting, one entry per step.

    Raises:
        ScentFieldError: if the revealed history is not playable.
    """
    return [(here, there) for _, here, there in _walk(start, axes, role, plays)]


def trail_snapshots(
    cells: Sequence[Position],
    board_size: int,
    intensity: float = CENTRE_INTENSITY,
    grid_size: int = GRID_SIZE,
    falloff: Falloff = DEFAULT_FALLOFF,
) -> list[dict[str, float]]:
    """The wire field an agent standing on each of ``cells`` in turn would show.

    Emission happens on **every** action, standing still included — the
    rulebook's field is laid down by occupying a cell, not by leaving one — and
    decay fires **once per full turn**, after the snapshot for that turn has
    been taken. Snapshotting before decaying is what makes the field an agent
    transmits at step *t* the field it actually laid at step *t*.
    """
    trail = Trail()
    snapshots = []
    for cell in cells:
        trail.deposit(emission(cell, board_size, intensity, grid_size, falloff))
        snapshots.append(trail.snapshot())
        trail.decay()
    return snapshots


def audit_scent(
    start: BoardState,
    axes: AxisConvention,
    role: str,
    plays: Sequence[StepPlay],
    *,
    require_bound: bool = True,
    falloff: Falloff = DEFAULT_FALLOFF,
) -> tuple[str, ...]:
    """Re-derive the opponent's trail and say where it disagrees with theirs."""
    failures: list[str] = []
    trail = Trail()
    try:
        for play, _, theirs in _walk(start, axes, role, plays):
            trail.deposit(emission(theirs, start.grid_size, falloff=falloff))
            expected = trail.snapshot()
            trail.decay()
            failures.extend(_disagreements(play, expected, start.grid_size, require_bound))
    except ScentFieldError as exc:
        failures.append(str(exc))
    return tuple(failures)


def _disagreements(
    play: StepPlay, expected: dict[str, float], board_size: int, require_bound: bool
) -> list[str]:
    """What is wrong with one step's disclosed field, if anything."""
    if play.disclosed is None:
        if not require_bound:
            return []
        return [
            f"step {play.step}: no scent field was disclosed, so nothing they emitted can "
            "be checked; unverifiable scent is refused rather than believed"
        ]
    try:
        check_field(play.disclosed, board_size)
    except ScentFieldError as exc:
        return [f"step {play.step}: {exc}"]
    if play.disclosed != expected:
        return [
            f"step {play.step}: the disclosed scent field is not the one their own revealed "
            f"moves produce ({_where(play.disclosed)} against {_where(expected)}); a hint may "
            "lie, a trail may not"
        ]
    return []


def _where(field: dict[str, float]) -> str:
    """The peak of a field, for an accusation the other side can check."""
    if not field:
        return "an empty field"
    cell = min(field, key=lambda key: (-field[key], key))
    return f"peak {field[cell]} at {cell}"
