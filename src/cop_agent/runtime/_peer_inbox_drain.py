"""Inbox draining and record matching helpers for runtime/peer.py."""

import queue
import time
from typing import Any

Record = dict[str, Any]


class PeerTimeout(RuntimeError):
    """Raised when the opponent did not say something in time."""


def drain_inbox(
    inbox: "queue.Queue[Any]",
    step: int | None,
    what: str,
    timeout: float,
    opponent: str,
    deadline: float | None = None,
) -> Any:
    remaining = timeout if deadline is None else max(deadline - time.monotonic(), 0.0)
    try:
        return inbox.get(timeout=remaining)
    except queue.Empty as exc:
        where = "" if step is None else f" for step {step}"
        raise PeerTimeout(
            f"waited {timeout:g}s for the {opponent}'s {what}{where} and it never came"
        ) from exc


def foreign_record(record: Record, game_uid: str, sub_game: int) -> bool:
    return bool(
        record.get("game_uid", game_uid) != game_uid or record.get("sub_game", sub_game) != sub_game
    )
