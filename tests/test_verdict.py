import json
from collections.abc import Callable
from pathlib import Path
from typing import Any
from cop_agent.domain.board import BoardState
from cop_agent.domain.crypto import commit_of, step_record
from cop_agent.infra.match_log import MatchLog
from cop_agent.ui.replay import check_step, load
from cop_agent.ui.verdict import Attestation, Stamp, walk
def sealed_log(
    tmp_path: Path, steps: int = 4, corrupt: int | None = None, unopened: int = 0
) -> Path:
    log = MatchLog(game_id="uoh26-s82kma9e", sub_game=2, role="police")
    for step in range(1, steps + 1):
        board = BoardState(
            grid_size=8, cop=(1, step), thief=(6, 5), barriers=frozenset(), step=step
        )
        record = step_record(board, "police", "N", "truth", f"step {step}")
        secret = f"{step:032x}"
        log.commit(step, commit_of(record, secret))
        log.reveal(step, {**record, "move": "S"} if step == corrupt else record)
        if step <= steps - unopened:
            log.disclose(step, secret)
    return log.write(tmp_path)
def hand_edited(path: Path, change: Callable[[dict[str, Any]], None]) -> Path:
    body = json.loads(path.read_text())
    change(body)
    path.write_text(json.dumps(body))
    return path
