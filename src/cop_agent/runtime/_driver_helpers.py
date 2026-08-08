"""Helper functions for runtime/driver.py: opponent awaiting and side parsing."""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..infra.declaration import Team
from ..infra.handshake import Greeting, Peering
from .orchestrator import Orchestrator

DEFAULT_PATIENCE = 180.0


class StartupTimeout(RuntimeError):
    """Raised when the opponent never came up."""


def _side(block: dict[str, Any]) -> Team:
    repos = block.get("repos", {})
    return Team(
        name=str(block.get("group_name", "")),
        members=tuple(str(m) for m in block.get("members", [])),
        cop_repo=str(repos.get("cop", "")),
        thief_repo=str(repos.get("thief", "")),
    )


def _us(private: dict[str, Any]) -> Team:
    return _side(private.get("game", {}))


def _them(private: dict[str, Any]) -> Team:
    return _side(private.get("teams", {}).get("them", {}))


def await_opponent(
    orchestrator: Orchestrator,
    ours: Greeting,
    directory: Path,
    game_id: str,
    patience: float = DEFAULT_PATIENCE,
    pause: float = 3.0,
    now: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> Peering:
    deadline = now() + patience
    attempts = 0
    while not orchestrator.try_announce(ours):
        attempts += 1
        if now() >= deadline:
            raise StartupTimeout(
                f"the opponent never came up: {attempts} attempts over {patience:g}s. "
                "Their agent has to be running and their tunnel forwarding to it — "
                "ask them to run `check`, and confirm the port their tunnel points at "
                "matches the one their agent listens on"
            )
        if attempts == 1:
            print("  waiting for the opponent to come up…", flush=True)
        sleep(pause)
    return orchestrator.open_series(ours, directory, game_id)
