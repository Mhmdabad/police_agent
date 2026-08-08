"""Helper functions for decoy selection and self-contradiction vetting in domain/bluff.py."""

import random
from dataclasses import dataclass

from .board import BoardState, Position
from .credibility import CONTRADICTION, FRESH_TRACE

INTENTS = ("truth", "lie")


def decoy(truth: Position, state: BoardState, rng: random.Random | None = None) -> Position:
    """A cell to lie about: the corner furthest from where we actually are."""
    del rng
    last = state.grid_size - 1
    corners = ((0, 0), (0, last), (last, 0), (last, last))
    return max(corners, key=lambda c: (abs(c[0] - truth[0]) + abs(c[1] - truth[1]), -c[0], -c[1]))


def plausible_decoy(
    truth: Position, state: BoardState, own_field: dict[Position, float]
) -> Position:
    """A cell to lie about that our own trail already supports."""
    away = {
        cell: value
        for cell, value in own_field.items()
        if abs(cell[0] - truth[0]) + abs(cell[1] - truth[1]) >= state.grid_size // 2
    }
    if not away:
        return decoy(truth, state)
    return min(away, key=lambda cell: (-away[cell], cell))


class SelfContradictionError(ValueError):
    """Raised when a hint we are about to send is refuted by our own field."""


@dataclass(frozen=True, slots=True)
class Bluff:
    """One turn's verbal output: what we said, and what we meant by it."""

    intent: str
    text: str
    about: Position

    def __post_init__(self) -> None:
        if self.intent not in INTENTS:
            raise ValueError(f"intent must be one of {INTENTS}, got {self.intent!r}")


def speak(
    truth: Position,
    state: BoardState,
    seen_from: Position,
    intent: str = "truth",
    rng: random.Random | None = None,
    own_field: dict[Position, float] | None = None,
) -> Bluff:
    if intent not in INTENTS:
        raise ValueError(f"intent must be one of {INTENTS}, got {intent!r}")
    if intent == "truth":
        about = truth
    elif own_field:
        about = plausible_decoy(truth, state, own_field)
    else:
        about = decoy(truth, state, rng)
    from .bluff import compose

    return Bluff(intent=intent, text=compose(about, state, seen_from, rng), about=about)


def contradicts_our_field(bluff: Bluff, own_field: dict[Position, float], predicted: float) -> bool:
    measured = max((own_field.get(cell, 0.0) for cell in _claimed(bluff)), default=0.0)
    return predicted > 0.0 and (predicted - measured) / predicted >= CONTRADICTION


def _claimed(bluff: Bluff) -> tuple[Position, ...]:
    row, col = bluff.about
    return tuple((row + drow, col + dcol) for drow in (-1, 0, 1) for dcol in (-1, 0, 1))


def vet(bluff: Bluff, own_field: dict[Position, float], predicted: float = FRESH_TRACE) -> Bluff:
    if bluff.intent == "truth":
        return bluff
    if contradicts_our_field(bluff, own_field, predicted):
        raise SelfContradictionError(
            f"our own field refutes {bluff.about}; the opponent would convict on arrival"
        )
    return bluff
