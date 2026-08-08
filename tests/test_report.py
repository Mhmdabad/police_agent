import base64
import json
from email import message_from_bytes
from email.policy import default as default_policy
from pathlib import Path
import pytest
import cop_agent
from cop_agent.infra.report import (
    LECTURER,
    SCHEMA_VERSION,
    Message,
    Report,
    ReportError,
    Repositories,
    SubGameResult,
)
REPOS = Repositories(
    cop_repo="https://github.com/Mhmdabad/police_agent",
    thief_repo="https://github.com/Mhmdabad/theif_agent",
    opponent_cop_repo="https://github.com/other/police",
    opponent_thief_repo="https://github.com/other/thief",
)
def result(sub_game: int = 1, cop: int = 100, thief: int = 0) -> SubGameResult:
    return SubGameResult(
        sub_game=sub_game,
        cop_score=cop,
        thief_score=thief,
        commit_hash=f"{sub_game:040x}",
        steps=17,
    )
def report(**overrides: object) -> Report:
    fields: dict[str, object] = {
        "game_id": "uoh26-s82kma9e",
        "role": "police",
        "team": "uoh26-cops",
        "opponent_team": "uoh26-others",
        "repositories": REPOS,
        "sub_games": (result(1), result(2, cop=0, thief=80)),
        "total_tokens": 41_233,
        "agreed": True,
    }
    fields.update(overrides)
    return Report(**fields)  # type: ignore[arg-type]
