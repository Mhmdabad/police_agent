import hashlib
import json
import re
import secrets
from pathlib import Path
from typing import Any
import pytest
from cop_agent.domain.board import BoardState
from cop_agent.domain.crypto import (
    NONCE_BYTES,
    CryptoError,
    audit,
    board_terms,
    canonical,
    commit_of,
    nonce,
    seal,
    step_record,
    verify,
)
from cop_agent.shared.config import canonical_bytes
SAMPLE = {"step": 3, "move": "N", "intent": "lie", "hint": "heading uptown"}
SRC = Path(__file__).parents[1] / "src" / "cop_agent"
BOARD = BoardState(
    grid_size=8, cop=(1, 2), thief=(6, 5), barriers=frozenset({(3, 3), (0, 1)}), step=4
)
