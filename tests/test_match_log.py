import json
from pathlib import Path
import pytest
from cop_agent.infra.match_log import SLOTS, MatchLog, MatchLogError
from cop_agent.shared.naming import NamingError
DIGEST = "a" * 64
NONCE = "0" * 32
OPENED = {"move": "N", "intent": "lie", "hint": "heading uptown", "barrier_placed": None}
def log() -> MatchLog:
    return MatchLog(game_id="uoh26-s82kma9e", sub_game=3, role="police")
def played(steps: int = 2) -> MatchLog:
    written = log()
    for step in range(1, steps + 1):
        written.commit(step, DIGEST)
        written.reveal(step, OPENED)
        written.disclose(step, NONCE)
    return written
def sealed_log(steps: int = 2, disclose: bool = True) -> MatchLog:
    log = MatchLog(
        game_id="uoh26-s82kma9e",
        sub_game=1,
        role="police",
        game_uid="u-0001",
        config_sha256="c" * 64,
    )
    for step in range(1, steps + 1):
        log.commit(step, f"{step:064x}")
        log.reveal(step, {"move": "N"})
        if disclose:
            log.disclose(step, f"{step:032x}")
    return log
