# mypy: ignore-errors
# ruff: noqa
from __future__ import annotations
import argparse
import json
import sys
import tomllib
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any
from .infra.inboxes import TOOL_NAMES, PeerInboxes
from .infra.mcp_client import ClientSettings
from .infra.mcp_server import SERVER_NAME, ServerSettings, build, serve
from .infra.tunnel import NotPublicError, discover, read_ngrok_api
from .shared.config import SHARED_CONFIG, series_length
from .shared.config import load as load_shared

MAX_DEPTH = 8


def safely_describe(exc: BaseException) -> str:
    try:
        return describe_failure(exc)
    except Exception as broke:  # noqa: BLE001 - a broken reporter must still report
        return f"{exc!r} (the failure description itself failed: {broke!r})"


def describe_failure(exc: BaseException) -> str:
    return _describe(exc, set(), 0)


def _describe(exc: BaseException, seen: set[int], depth: int) -> str:
    if id(exc) in seen or depth > MAX_DEPTH:
        return type(exc).__name__
    seen.add(id(exc))
    inner = getattr(exc, "exceptions", None)
    if isinstance(inner, (list, tuple)) and inner:
        parts = [_describe(one, seen, depth + 1) for one in inner]
        return "; ".join(dict.fromkeys(parts))
    said = "; ".join(part for part in (str(a).strip() for a in exc.args) if part)
    if not said:
        said = str(exc).strip()
    label = type(exc).__name__
    if said:
        return said if label in said else f"{said} ({label})"
    because = exc.__cause__ or exc.__context__
    if because is not None:
        return f"{label}, which carried no message; caused by {_describe(because, seen, depth + 1)}"
    return f"{label} with no message — nothing recorded why, which is itself the bug"


def play(
    arguments: argparse.Namespace,
    private: dict[str, Any],
    settings: ServerSettings,
    inboxes: PeerInboxes,
    environ: dict[str, str],
) -> int:  # pragma: no cover - drives a live opponent
    import threading
    from .runtime.driver import open_match

    threading.Thread(target=serve, args=(build(inboxes), settings), daemon=True).start()
    print(f"serving on {settings.host}:{settings.port}", flush=True)
    try:
        written = open_match(
            inboxes=inboxes,
            private=private,
            environ=environ,
            game_id=arguments.game_id,
            directory=arguments.out,
            rehearsal=arguments.rehearse,
        )
    except Exception as exc:  # noqa: BLE001 - a match failure is a message, not a traceback
        print(f"the match did not finish: {safely_describe(exc)}", file=sys.stderr)
        return 1
    for path in written:
        print(f"  wrote {path}")
    print("\nNothing has been emailed. Agree the result with the opponent first,")
    print("then send it deliberately — FR-7.16.")
    return 0


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
