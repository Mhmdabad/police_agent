import pytest
from cop_agent.infra.inboxes import ACK, TOOL_NAMES, PeerInboxes, register
from cop_agent.infra.protocol import (
    CONTROL_KINDS,
    ROLES,
    AuditPayload,
    ControlMessage,
    TurnMessage,
)
from cop_agent.infra.validation import InvalidPayloadError
TURN = {
    "step": 3,
    "sender": "police",
    "hint": "closing in near Times Square",
    "smell_grid": {"2,3": 0.9, "2,4": 0.6},
    "commit": "a" * 64,
    "timestamp": "2026-08-03T09:00:00+00:00",
    "game_uid": "series-123",
    "sub_game": 2,
}
class RecordingHost:
    def __init__(self) -> None:
        self.registered: list[str] = []
    def tool(self, fn: object) -> object:
        self.registered.append(getattr(fn, "__name__", str(fn)))
        return fn
