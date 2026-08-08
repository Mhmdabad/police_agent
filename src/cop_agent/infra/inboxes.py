# mypy: ignore-errors
# ruff: noqa
from ._inboxes_peerinboxes_1 import _PeerInboxesMixin1, _install as _install_inboxes_peerinboxes_1
from ._inboxes_peerinboxes_2 import _PeerInboxesMixin2, _install as _install_inboxes_peerinboxes_2
from ._inboxes_peerinboxes_3 import _PeerInboxesMixin3, _install as _install_inboxes_peerinboxes_3
import hashlib
import queue
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol
from ..shared.config import canonical_bytes
from .protocol import AuditPayload, ControlMessage, TurnMessage
def fingerprint(turn: TurnMessage) -> str:
    return hashlib.sha256(canonical_bytes(turn.to_dict())).hexdigest()
DIGEST_KEY = "config_sha256"
SERIES_KEY = "game_uid"
SCENT_KEY = "scent_lock"
SCENT_DIGEST_KEY = "scent_sha256"
RETRY_KEY = "retry"
ACK: dict[str, Any] = {"ok": True}
TOOL_NAMES: tuple[str, ...] = ("negotiate", "receive_turn", "submit_audit", "receive_control")
@dataclass
class PeerInboxes(_PeerInboxesMixin1, _PeerInboxesMixin2, _PeerInboxesMixin3):
    agreements: "queue.Queue[dict[str, Any]]" = field(default_factory=queue.Queue)
    digests: "queue.Queue[dict[str, Any]]" = field(default_factory=queue.Queue)
    scent_locks: "queue.Queue[dict[str, Any]]" = field(default_factory=queue.Queue)
    turns: "queue.Queue[TurnMessage]" = field(default_factory=queue.Queue)
    audits: "queue.Queue[AuditPayload]" = field(default_factory=queue.Queue)
    controls: "queue.Queue[ControlMessage]" = field(default_factory=queue.Queue)
    rejected: list[str] = field(default_factory=list)
    accepted_turns: dict[tuple[str, int, str, int], str] = field(default_factory=dict)
    accepted_reveals: dict[tuple[str, int, str, int], str] = field(default_factory=dict)
    hint_max_words: int = 15
    game_uid: str = ""
    sub_game: int = 0
    duplicates: list[str] = field(default_factory=list)
    deferred: list[str] = field(default_factory=list)
class ToolHost(Protocol):
    def tool(self, fn: Callable[..., dict[str, Any]]) -> object: ...
def register(host: ToolHost, inboxes: PeerInboxes) -> tuple[str, ...]:
    host.tool(inboxes.negotiate)
    host.tool(inboxes.receive_turn)
    host.tool(inboxes.submit_audit)
    host.tool(inboxes.receive_control)
    return TOOL_NAMES
_install_inboxes_peerinboxes_1(globals())
_install_inboxes_peerinboxes_2(globals())
_install_inboxes_peerinboxes_3(globals())
