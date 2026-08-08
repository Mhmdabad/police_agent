"""Scent emission: the signal an agent cannot help leaving.

Emits Euclidean Gaussian (or Chebyshev) falloff centered on agent position.
"""

import math
from collections.abc import Callable

from ..shared.appendix_f import book_value
from .board import Position

PRECISION = 3
"""Decimal places every intensity is rounded to.

Not cosmetic. Two peers running the same formula in different float orders
disagree in the last bits, and the disagreement is permanent because the field
is hashed into the pre-series lock.
"""

SIGMA = 1.15
"""Spread of the Gaussian, fitted to figure 4 rather than chosen.

The figure prints the field to two decimals; ``0.9 * exp(-(dr**2+dc**2) /
(2*sigma**2))`` reproduces every printed value for sigma in [1.148, 1.1544],
and 1.15 is the round number inside that interval. It is derived from the
rulebook, not tuned for play, because it is an agreement term rather than a
strategy parameter.
"""


def _fixed_float(section: str, key: str) -> float:
    value = book_value(section, key)
    if not isinstance(value, int | float):
        raise TypeError(f"{section}.{key} is {type(value).__name__}, not a number")
    return float(value)


CENTRE_INTENSITY: float = _fixed_float("pheromones", "pheromone_center_intensity")
"""Appendix F centre intensity. *Fixed* - deviating disqualifies the team."""

GRID_SIZE: int = int(_fixed_float("pheromones", "pheromone_grid_size"))
"""Appendix F emission width. *Fixed*. Odd, so the emitter has a centre cell."""

Falloff = Callable[[int, int, float, int], float]
"""A falloff model: ``(dr, dc, centre_intensity, grid_size) -> intensity``."""


def gaussian(offset_row: int, offset_col: int, intensity: float, grid_size: int) -> float:
    """The rulebook's radial hill. Figure 4, PDF p. 44.

    ``grid_size`` is unused: the hill's shape is set by :data:`SIGMA`, and the
    grid only decides where it is cut off. Kept in the signature so every
    falloff model is interchangeable.
    """
    del grid_size
    squared = offset_row * offset_row + offset_col * offset_col
    return intensity * math.exp(-squared / (2 * SIGMA * SIGMA))


def chebyshev(offset_row: int, offset_col: int, intensity: float, grid_size: int) -> float:
    """The reference implementation's square terrace.

    Selectable so it can be agreed at negotiation against an opponent running
    the reference code, which is a likely enough case to be worth supporting
    without a code change. Rings are 0.9, 0.6, 0.3.
    """
    step = intensity / (grid_size // 2 + 1)
    return intensity - step * max(abs(offset_row), abs(offset_col))


CHEBYSHEV: Falloff = chebyshev
GAUSSIAN: Falloff = gaussian
DEFAULT_FALLOFF: Falloff = gaussian
"""The rulebook's model, used unless a series is negotiated otherwise."""

MODELS: dict[str, Falloff] = {"gaussian": gaussian, "chebyshev": chebyshev}
"""Named models, so a negotiated agreement can name one on the wire."""


def emission(
    centre: Position,
    board_size: int,
    intensity: float = CENTRE_INTENSITY,
    grid_size: int = GRID_SIZE,
    falloff: Falloff = DEFAULT_FALLOFF,
) -> dict[Position, float]:
    """The field laid down by an agent standing on ``centre``.

    Clipped to the board, so a corner emission is a quarter of a full one.
    Cells that fall to zero are still returned: an explicit zero and an absent
    key mean different things once fields are merged, and collapsing them here
    would make the wire form depend on where the emitter happened to stand.
    """
    half = grid_size // 2
    field: dict[Position, float] = {}
    for offset_row in range(-half, half + 1):
        for offset_col in range(-half, half + 1):
            cell = (centre[0] + offset_row, centre[1] + offset_col)
            if 0 <= cell[0] < board_size and 0 <= cell[1] < board_size:
                value = falloff(offset_row, offset_col, intensity, grid_size)
                field[cell] = round(max(0.0, value), PRECISION)
    return field


def numeric_example(
    intensity: float = CENTRE_INTENSITY,
    grid_size: int = GRID_SIZE,
    falloff: Falloff = DEFAULT_FALLOFF,
) -> str:
    """The worked example exchanged at the pre-series lock.

    The rulebook requires both teams to swap the emission model *with a
    concrete numeric example* and hash the agreement. A formula agreed in prose
    is a formula two teams can implement differently; a formula agreed
    alongside the numbers it produces is not.

    Reports whichever model is in force, so a negotiated Chebyshev series
    exchanges Chebyshev numbers rather than the ones we prefer.
    """
    name = next((key for key, model in MODELS.items() if model is falloff), "custom")
    half = grid_size // 2
    rows = []
    for offset_row in range(-half, half + 1):
        rows.append(
            " ".join(
                f"{round(max(0.0, falloff(offset_row, offset_col, intensity, grid_size)), 2):.2f}"
                for offset_col in range(-half, half + 1)
            )
        )
    return f"{name} {grid_size}x{grid_size}, centre tau={intensity}:\n" + "\n".join(rows)
