import json
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any
import pytest
from cop_agent.domain.board import BoardState
from cop_agent.domain.crypto import commit_of, step_record
from cop_agent.infra.match_log import MatchLog
from cop_agent.ui.replay import load
from cop_agent.ui.verdict import Stamp, walk
STEPS = 4
Edit = Callable[[dict[str, Any]], None]
def honest_log(tmp_path: Path, steps: int = STEPS) -> Path:
    log = MatchLog(game_id="uoh26-s82kma9e", sub_game=2, role="police")
    for step in range(1, steps + 1):
        board = BoardState(
            grid_size=8,
            cop=(1, step),
            thief=(6, 5),
            barriers=frozenset({(3, 3)}) if step > 1 else frozenset(),
            step=step,
        )
        record = step_record(board, "police", "N", "truth", f"step {step}", (3, 3))
        secret = f"{step:032x}"
        log.commit(step, commit_of(record, secret))
        log.reveal(step, record)
        log.disclose(step, secret)
    return log.write(tmp_path)
def by_hand(path: Path, edit: Edit) -> Path:
    body = json.loads(path.read_text())
    edit(body)
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
    return path
def stamp_after(tmp_path: Path, edit: Edit) -> Stamp:
    return walk(load(by_hand(honest_log(tmp_path), edit))).stamp
def swapped(value: object) -> object:
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    if isinstance(value, str):
        return value + "x"
    if isinstance(value, list):
        return [*value, 0] if value else [0]
    if isinstance(value, dict):
        return {**value, "added": 0}
    if value is None:
        return 0
    raise AssertionError(f"no swap defined for {type(value).__name__}")
