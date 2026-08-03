"""The tools this peer exposes to its opponent.

This is the whole inbound surface. Everything arriving here comes from an
agent we do not control and have no reason to trust, so each tool returns a
structured result rather than raising across the wire, and none of them mutate
game state directly — they hand work to the runtime, which decides.

The tool set is deliberately small. Every endpoint is another thing an
opponent can probe, and another thing that must behave identically on both
sides for a match to be reconcilable at audit.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .validation import (
    InvalidPayloadError,
    reject_unknown_fields,
    require_choice,
    require_int,
    require_mapping,
    require_str,
)

PROTOCOL_VERSION = "1.0"
"""Bumped when the wire contract changes. Exchanged during the handshake."""


@dataclass(frozen=True, slots=True)
class ToolResult:
    """What every tool returns.

    A rejection is a *result*, not an exception. An exception crossing the wire
    tells the opponent only that something broke; a structured refusal tells
    them what and why, which is what makes a disputed result reconcilable
    rather than a stand-off.
    """

    ok: bool
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "detail": self.detail, "data": self.data}

    @classmethod
    def accept(cls, **data: object) -> "ToolResult":
        return cls(ok=True, data=dict(data))

    @classmethod
    def refuse(cls, detail: str) -> "ToolResult":
        return cls(ok=False, detail=detail)


@dataclass(frozen=True, slots=True)
class PeerIdentity:
    """Who we are, as announced in the handshake."""

    group_id: str
    role: str
    protocol_version: str = PROTOCOL_VERSION


class ToolSurface:
    """The inbound tools, independent of any MCP framework.

    Kept free of FastMCP so the contract can be tested directly. Registration
    with a server is a separate, thin step.
    """

    def __init__(
        self,
        identity: PeerIdentity,
        config_digest: str,
        state_digest: Callable[[], str],
    ) -> None:
        self._identity = identity
        self._config_digest = config_digest
        self._state_digest = state_digest

    def ping(self) -> ToolResult:
        """Liveness probe. Carries no game state deliberately."""
        return ToolResult.accept(protocol_version=self._identity.protocol_version)

    def dispatch(self, tool: str, payload: object) -> ToolResult:
        """Validate an inbound call and route it, refusing rather than raising.

        The single entry point for anything arriving from the opponent. A
        malformed payload must never become an unhandled exception: a crash
        mid-turn is a technical loss scoring zero for both sides, so a peer
        that can be crashed by hostile input hands its opponent a way to void
        any match it is losing.
        """
        cells = {"row": (0, 1000), "col": (0, 1000), "step": (0, 10_000)}
        try:
            body = require_mapping(payload)
            match tool:
                case "ping":
                    reject_unknown_fields(body, frozenset())
                    return self.ping()
                case "handshake":
                    fields = frozenset({"group_id", "role", "protocol_version"})
                    reject_unknown_fields(body, fields)
                    return self.handshake(
                        require_str(body, "group_id"),
                        require_choice(body, "role", frozenset({"cop", "thief"})),
                        require_str(body, "protocol_version"),
                    )
                case "negotiate_config":
                    reject_unknown_fields(body, frozenset({"config_sha256"}))
                    return self.negotiate_config(require_str(body, "config_sha256"))
                case "declare_barrier":
                    reject_unknown_fields(body, frozenset({"row", "col", "step"}))
                    return self.declare_barrier(
                        require_int(body, "row", minimum=cells["row"][0], maximum=cells["row"][1]),
                        require_int(body, "col", minimum=cells["col"][0], maximum=cells["col"][1]),
                        require_int(
                            body, "step", minimum=cells["step"][0], maximum=cells["step"][1]
                        ),
                    )
                case "capture_claim":
                    reject_unknown_fields(body, frozenset({"row", "col", "step", "basis"}))
                    return self.capture_claim(
                        require_int(body, "row", minimum=cells["row"][0], maximum=cells["row"][1]),
                        require_int(body, "col", minimum=cells["col"][0], maximum=cells["col"][1]),
                        require_int(
                            body, "step", minimum=cells["step"][0], maximum=cells["step"][1]
                        ),
                        require_choice(
                            body, "basis", frozenset({"overlap", "trapping", "enclosure"})
                        ),
                    )
                case "get_state_digest":
                    reject_unknown_fields(body, frozenset())
                    return self.get_state_digest()
                case _:
                    return ToolResult.refuse(f"unknown tool {tool!r}")
        except InvalidPayloadError as exc:
            return ToolResult.refuse(str(exc))

    def handshake(self, group_id: str, role: str, protocol_version: str) -> ToolResult:
        """Exchange identity and refuse a protocol mismatch.

        A version mismatch is refused before a match starts rather than
        discovered mid-turn, where it would present as arbitrary rejections.
        """
        if protocol_version != self._identity.protocol_version:
            return ToolResult.refuse(
                f"protocol {protocol_version} != ours {self._identity.protocol_version}"
            )
        if role == self._identity.role:
            return ToolResult.refuse(f"both peers claim the role {role!r}")
        return ToolResult.accept(
            group_id=self._identity.group_id,
            role=self._identity.role,
            protocol_version=self._identity.protocol_version,
        )

    def negotiate_config(self, config_sha256: str) -> ToolResult:
        """Compare the opponent's signed config digest with ours.

        A mismatch means the two peers would enforce different physics, so the
        only safe answer is to refuse to play. Failing here costs a match that
        was never playable; failing to fail here costs a match that both sides
        thought they played correctly.
        """
        if config_sha256 != self._config_digest:
            return ToolResult.refuse(
                f"config digest mismatch: theirs {config_sha256[:12]}… "
                f"ours {self._config_digest[:12]}… — refusing to play"
            )
        return ToolResult.accept(config_sha256=self._config_digest)

    def declare_barrier(self, row: int, col: int, step: int) -> ToolResult:
        """Announce a barrier placement, truthfully and with its exact cell.

        The rulebook is unusually blunt here: every placement must be
        announced, no barrier may be placed in secret, and the cop may not lie
        about the location. Both are disqualification offences, and the audit
        re-checks each declaration against the sealed commitment.

        So this method exists to be called on **every** placement. It carries
        the position and the step rather than a bare acknowledgement, because
        the opponent must be able to reconstruct the board from declarations
        alone in order to validate ours against theirs.
        """
        return ToolResult.accept(row=row, col=col, step=step, declared_by=self._identity.role)

    def capture_claim(self, row: int, col: int, step: int, basis: str) -> ToolResult:
        """Assert a capture, naming the cell, the step and the grounds.

        The claim places the thief under a cryptographic obligation to answer
        truthfully — and it binds this agent exactly as hard. A claim must be
        derivable from verified board state; a false one is exposed at the log
        audit and disqualifies the team **with no appeal**.

        ``basis`` names which of the three routes is being claimed: overlap,
        trapping placement, or enclosure. A bare "I captured you" is not
        checkable without replaying the whole match, whereas a named basis can
        be verified against the opponent's own copy of the board immediately.
        """
        return ToolResult.accept(row=row, col=col, step=step, basis=basis)

    def get_state_digest(self) -> ToolResult:
        """Our view of the board, for cross-checking.

        A digest rather than the state itself: the opponent must not learn our
        position, only whether our views agree.
        """
        return ToolResult.accept(state_digest=self._state_digest())
