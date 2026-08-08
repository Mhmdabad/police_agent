import random
import pytest
from cop_agent.domain.bluff import (
    COMPASS,
    TEMPLATES,
    Bluff,
    SelfContradictionError,
    bearing,
    compose,
    contradicts_our_field,
    decoy,
    nearest_landmark,
    plausible_decoy,
    speak,
    vet,
)
from cop_agent.domain.board import BoardState
from cop_agent.domain.hints import DIRECTIONS, LANDMARKS, MAX_WORDS, NUMERIC, parse
from cop_agent.domain.scent import emission
from cop_agent.domain.trail import Trail
BOARD = BoardState(cop=(0, 0), thief=(5, 1), grid_size=7)
def every_hint() -> list[str]:
    return [
        compose(cell, BOARD, (3, 3), random.Random(seed))
        for seed in range(len(TEMPLATES))
        for cell in ((0, 0), (5, 1), (6, 6), (3, 3), (0, 6))
    ]
