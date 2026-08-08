import json
from pathlib import Path
import pytest
from cop_agent.infra.declaration import (
    DeclarationError,
    Endpoints,
    MatchDeclaration,
    Team,
    build,
    declare_match,
)
from cop_agent.infra.step_zero import UNSIGNED, Hardware, Provenance, verify_signature
KEY = "a-key-the-course-has-not-supplied-yet"
US = Team(
    name="uoh26-cops",
    members=("Mohammed Abad",),
    cop_repo="https://github.com/Mhmdabad/police_agent",
    thief_repo="https://github.com/Mhmdabad/theif_agent",
)
THEM = Team(
    name="uoh26-others",
    members=("A Person", "Another"),
    cop_repo="https://github.com/other/police",
    thief_repo="https://github.com/other/thief",
)
WHERE = Endpoints(ours="https://a.ngrok.io/mcp", theirs="https://b.ngrok.io/mcp")
HARDWARE = Hardware(
    os_name="Linux",
    logical_cores=8,
    cpu_max_mhz=3600.0,
    ram_mb=16384,
    gpu=None,
    vram_mb=None,
    llm_model="claude-haiku-4-5",
)
PROVENANCE = Provenance(
    code_version="1.0.0",
    group_name="uoh26-cops",
    sub_game=1,
    github_commit="a" * 40,
    dirty=False,
)
def declared(key: str | None = KEY, **overrides: object) -> MatchDeclaration:
    fields: dict[str, object] = {
        "game_id": "uoh26-s82kma9e",
        "game_uid": "u-0001",
        "role": "police",
        "us": US,
        "them": THEM,
        "endpoints": WHERE,
        "hardware": HARDWARE,
        "provenance": PROVENANCE,
        "llm_model": "claude-haiku-4-5",
        "token_ceiling": 200_000,
        "started_at": "2026-08-05T12:00:00Z",
        "key": key,
    }
    fields.update(overrides)
    return build(**fields)  # type: ignore[arg-type]
