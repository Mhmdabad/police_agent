import json
from pathlib import Path
from typing import Any
import pytest
from cop_agent.infra.artefacts import ArtefactError, ArtefactSet
from cop_agent.infra.config_file import LockedConfig, lock
from cop_agent.infra.declaration import Endpoints, MatchDeclaration, Team, build
from cop_agent.infra.match_log import MatchLog
from cop_agent.infra.report import Report, Repositories, SubGameResult
from cop_agent.infra.step_zero import Hardware, Provenance
GAME_ID = "uoh26-s82kma9e"
UID = "u-0001"
TEAMS = ("uoh26-cops", "uoh26-others")
REPOS = Repositories(
    cop_repo="https://github.com/Mhmdabad/police_agent",
    thief_repo="https://github.com/Mhmdabad/theif_agent",
    opponent_cop_repo="https://github.com/other/police",
    opponent_thief_repo="https://github.com/other/thief",
)
def parameters() -> dict[str, Any]:
    body = json.loads((Path(__file__).resolve().parent.parent / "config/game.json").read_text())
    assert isinstance(body, dict)
    return body
def a_declaration(game_id: str = GAME_ID, uid: str = UID) -> MatchDeclaration:
    return build(
        game_id=game_id,
        game_uid=uid,
        role="police",
        us=Team(
            name="uoh26-cops",
            members=("Mohammed Abad",),
            cop_repo=REPOS.cop_repo,
            thief_repo=REPOS.thief_repo,
        ),
        them=Team(
            name="uoh26-others",
            members=("Someone",),
            cop_repo=REPOS.opponent_cop_repo,
            thief_repo=REPOS.opponent_thief_repo,
        ),
        endpoints=Endpoints(ours="https://a.ngrok.io/mcp", theirs="https://b.ngrok.io/mcp"),
        hardware=Hardware(
            os_name="Linux",
            logical_cores=8,
            cpu_max_mhz=3600.0,
            ram_mb=16384,
            gpu=None,
            vram_mb=None,
            llm_model="claude-haiku-4-5",
        ),
        provenance=Provenance(
            code_version="1.0.0",
            group_name="uoh26-cops",
            sub_game=1,
            github_commit="a" * 40,
            dirty=False,
        ),
        llm_model="claude-haiku-4-5",
        token_ceiling=200_000,
        started_at="2026-08-05T12:00:00Z",
        key=None,
    )
def a_config(sub_game: int, game_id: str = GAME_ID, uid: str = UID) -> LockedConfig:
    return lock(
        game_id=game_id,
        game_uid=uid,
        sub_game=sub_game,
        parameters=parameters(),
        agreed_between=TEAMS,
    )
def a_log(sub_game: int, game_id: str = GAME_ID, uid: str = UID) -> MatchLog:
    log = MatchLog(
        game_id=game_id,
        sub_game=sub_game,
        role="police",
        game_uid=uid,
        config_sha256="c" * 64,
    )
    log.commit(1, f"{sub_game:064x}")
    log.reveal(1, {"move": "N"})
    log.disclose(1, f"{sub_game:032x}")
    return log
def a_result(sub_games: tuple[int, ...] = (1, 2), game_id: str = GAME_ID, uid: str = UID) -> Report:
    return Report(
        game_id=game_id,
        game_uid=uid,
        role="police",
        team="uoh26-cops",
        opponent_team="uoh26-others",
        repositories=REPOS,
        sub_games=tuple(
            SubGameResult(
                sub_game=number, cop_score=10, thief_score=0, commit_hash=f"{number:040x}"
            )
            for number in sub_games
        ),
        total_tokens=1234,
        agreed=True,
    )
def a_set(**overrides: object) -> ArtefactSet:
    fields: dict[str, object] = {
        "declaration": a_declaration(),
        "configs": (a_config(1), a_config(2)),
        "logs": (a_log(1), a_log(2)),
        "result": a_result(),
    }
    fields.update(overrides)
    return ArtefactSet(**fields)  # type: ignore[arg-type]
