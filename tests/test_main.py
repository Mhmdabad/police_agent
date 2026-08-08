import argparse
from collections.abc import Callable
from pathlib import Path
import pytest
from cop_agent.__main__ import (
    CONFIG,
    MAX_DEPTH,
    StartupError,
    describe,
    describe_failure,
    load_private,
    main,
    require_playable,
    safely_describe,
    where_we_are,
)
REPO = Path(__file__).resolve().parent.parent
NO_TUNNEL: dict[str, str] = {}
NO_NGROK = None
"""No ngrok probe at all.
Passing ``None`` is how :func:`~cop_agent.infra.tunnel.discover` is told not to
look. Left at the default, these checks probe the real ngrok API on this
machine and pass or fail depending on whether a tunnel happens to be running —
a test that reports the developer's desktop rather than the code.
"""
def where_we_are_url(environ: dict[str, str]) -> str:
    return where_we_are(environ, NO_NGROK)
def private() -> dict[str, object]:
    return load_private(REPO / CONFIG)
def record_play(seen: list[object]) -> Callable[..., int]:
    def play(*args: object) -> int:
        seen.append(args)
        return 0
    return play
