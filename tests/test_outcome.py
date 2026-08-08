import inspect
import random
import re
from pathlib import Path
from cop_agent.domain.actions import PlaceBarrier, apply_action
from cop_agent.domain.axes import ORIGIN_CORNERS, AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.domain.outcome import (
    DEFAULT_SURVIVAL_THRESHOLD,
    TechnicalLoss,
    capture_claim,
    claim_is_supported,
    is_capture_by_overlap,
    is_enclosure_capture,
    is_survival,
    is_trapping_capture,
    technical_loss_scores,
)
from cop_agent.domain.rules import advance_turn, apply_move, legal_moves
AXES = AxisConvention()
def make(**kw: object) -> BoardState:
    base: dict[str, object] = {"grid_size": 7, "cop": (0, 0), "thief": (3, 3)}
    base.update(kw)
    return BoardState(**base)  # type: ignore[arg-type]
SRC = Path(__file__).parents[1] / "src" / "cop_agent"
def board(**overrides: object) -> BoardState:
    fields: dict[str, object] = {
        "grid_size": 6,
        "cop": (0, 0),
        "thief": (3, 3),
        "barriers": frozenset(),
        "step": 1,
    }
    return BoardState(**{**fields, **overrides})  # type: ignore[arg-type]
