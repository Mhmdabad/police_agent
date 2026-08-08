import json
from pathlib import Path
import pytest
from cop_agent.domain.board import BoardState
from cop_agent.domain.crypto import commit_of, step_record
from cop_agent.infra.match_log import MatchLog
from cop_agent.ui.replay import Replay, ReplayError, check_step, load
OPENED = {"move": "N", "intent": "lie", "hint": "heading uptown", "barrier_placed": None}
def written(tmp_path: Path, steps: int = 4, unopened: int = 0) -> Path:
    log = MatchLog(game_id="uoh26-s82kma9e", sub_game=2, role="police")
    for step in range(1, steps + 1):
        log.commit(step, f"{step:064x}")
        log.reveal(step, OPENED)
        if step <= steps - unopened:
            log.disclose(step, f"{step:032x}")
    return log.write(tmp_path)
def edited(tmp_path: Path, change: object) -> Path:
    path = written(tmp_path)
    body = json.loads(path.read_text())
    if callable(change):
        change(body)
    path.write_text(json.dumps(body))
    return path
def sealed_log(tmp_path: Path, steps: int = 3, corrupt: int | None = None) -> Path:
    log = MatchLog(game_id="uoh26-s82kma9e", sub_game=2, role="police")
    for step in range(1, steps + 1):
        board = BoardState(
            grid_size=8, cop=(1, step), thief=(6, 5), barriers=frozenset(), step=step
        )
        record = step_record(board, "police", "N", "truth", f"step {step}")
        secret = f"{step:032x}"
        log.commit(step, commit_of(record, secret))
        log.reveal(step, {**record, "move": "S"} if step == corrupt else record)
        log.disclose(step, secret)
    return log.write(tmp_path)
