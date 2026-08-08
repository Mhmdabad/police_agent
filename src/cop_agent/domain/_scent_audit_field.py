"""Field checking and ScentFieldError definition for domain/scent_audit.py."""

import math
import re
from dataclasses import dataclass

from .actions import Action
from .board import Position
from .scent import CENTRE_INTENSITY, PRECISION

CELL = re.compile(r"^(0|[1-9][0-9]*),(0|[1-9][0-9]*)$")


class ScentFieldError(ValueError):
    """Raised when a scent field cannot be trusted, or cannot be re-derived."""


@dataclass(frozen=True, slots=True)
class StepPlay:
    """One step as the audit sees it: both actions, and what they disclosed."""

    step: int
    ours: Action
    theirs: Action | None
    disclosed: dict[str, float] | None


def check_field(wire: dict[str, float], board_size: int) -> dict[Position, float]:
    """Parse a received field, refusing anything we would not want to read."""
    if not isinstance(wire, dict):
        raise ScentFieldError(f"scent field must be an object, got {type(wire).__name__}")
    if len(wire) > board_size * board_size:
        raise ScentFieldError(
            f"scent field has {len(wire)} cells, more than the {board_size * board_size} "
            f"a {board_size}x{board_size} board contains"
        )
    field: dict[Position, float] = {}
    for key, value in wire.items():
        if not isinstance(key, str) or not CELL.match(key):
            raise ScentFieldError(f"cell key {key!r} is not 'row,col'")
        row, _, col = key.partition(",")
        cell = (int(row), int(col))
        if not (0 <= cell[0] < board_size and 0 <= cell[1] < board_size):
            raise ScentFieldError(f"cell {key!r} is off a {board_size}x{board_size} board")
        field[cell] = _intensity(key, value)
    return field


def _intensity(key: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ScentFieldError(f"intensity at {key!r} must be a number, got {type(value).__name__}")
    number = float(value)
    if not math.isfinite(number):
        raise ScentFieldError(f"intensity at {key!r} must be finite, got {number!r}")
    if number < 0.0:
        raise ScentFieldError(f"intensity at {key!r} is negative ({number!r})")
    if number > CENTRE_INTENSITY:
        raise ScentFieldError(f"intensity at {key!r} is {number!r}, above centre intensity")
    if number != round(number, PRECISION):
        raise ScentFieldError(f"intensity at {key!r} carries more precision than transmitted")
    return number
