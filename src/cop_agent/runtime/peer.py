# mypy: ignore-errors
# ruff: noqa
from ._peer_mcppeer_1 import _McpPeerMixin1, _install as _install_peer_mcppeer_1
from ._peer_mcppeer_2 import _McpPeerMixin2, _install as _install_peer_mcppeer_2
"""Carrying four ceremony phases over four MCP tools that are not the same four.

:mod:`.subgame` decides what must be said and in what order. This is how it
crosses the wire, and the mapping is the decision worth reading:

============  ==========================================================
Phase         How it travels
============  ==========================================================
Commit        ``receive_turn``, carrying the digest in a ``TurnMessage``.
Acknowledge   **the response to that call.** Not a message of its own.
Reveal        ``submit_audit``, one record, no nonce.
Final Reveal  ``submit_audit``, the nonces, once, at the end.
============  ==========================================================

**Acknowledge is the response, and that is the point.** The four tools are
fixed by the protocol we share with every other team, and inventing a fifth
would fail against all of them at first contact. ``receive_turn`` already
answers, and an acknowledgement *is* an answer: "I hold your commitment". So the
phase costs no new message and no interop risk. What it does cost is honesty
about a limit — the reference implementation returns a bare ``{"ok": true}``,
which carries no digest, so against a reference opponent we can confirm delivery
but not *which* commitment they hold. Against another agent running this code
the digest is there. The difference is recorded rather than papered over.

**Reveal and Final Reveal share ``submit_audit``** because it is the only tool
whose payload is a list of records, and they are told apart by shape: a reveal
has a ``move``, a final reveal has ``nonces``. Splitting them across tools would
have meant putting a reveal in ``receive_control``, whose four kinds are fixed.

``AuditPayload`` requires a **non-empty** ``result_claim``, which is a sensible
demand of an end-of-game message and an awkward one for a mid-game reveal: at
step two nobody is claiming anything. Sending :data:`UNDECIDED` rather than
relaxing the schema keeps the wire contract we share with every other team, and
says something true — the sub-game is still running. Left empty, the opponent
refuses the message, nothing is enqueued, and both sides wait for each other
until their deadlines expire. That is not a hypothetical; it is what happened
the first time this ran.

**Receiving is draining an inbox, not calling anything.** The opponent pushes to
our server; :class:`~..infra.inboxes.PeerInboxes` queues it; this waits with a
deadline. A wait that ran out is not an error here — it is handed upward as one,
because a peer that stopped answering is a technical loss and that judgement
belongs where the match is scored.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..infra.ceremony import Acknowledgement
from ..infra.inboxes import PeerInboxes
from ..infra.mcp_client import OpponentClient

Record = dict[str, Any]
Wanted = Callable[[Record], bool]


UNDECIDED = "in_progress"
"""What a mid-game reveal claims about the result: nothing yet."""


class PeerTimeout(RuntimeError):
    """Raised when the opponent did not say something in time.

    The caller converts this into a technical loss. Not retried here: the
    client's budget is the whole allowance, and a second wait on top of it
    would be a deadline nobody agreed to.
    """




@dataclass
class McpPeer(_McpPeerMixin1, _McpPeerMixin2):
    """The opponent, over the wire."""

    role: str
    client: OpponentClient
    inboxes: PeerInboxes
    game_uid: str
    sub_game: int
    now: str = ""
    timeout: float = 30.0
    hint_max_words: int = 15
    acks: dict[int, Acknowledgement] = field(default_factory=dict, init=False)
    result_claim: str = ""
    """What we claim the sub-game's result was. Set before the final reveal."""

    reference_acks: list[int] = field(default_factory=list, init=False)
    """Steps where their acknowledgement carried no digest. See the module docs."""

    # --- phase 1: commit ----------------------------------------------------

    # --- phase 2: acknowledge -----------------------------------------------

    # --- phase 3: reveal ----------------------------------------------------

    # --- phase 4: final reveal ----------------------------------------------

    # --- plumbing -----------------------------------------------------------

    _held: list[Record] = field(default_factory=list, init=False)
    quarantined: list[Record] = field(default_factory=list, init=False)
    """Records that could not belong to this sub-game, kept rather than acted on.

    The door queues only what names our exact binding, so nothing here should
    ever arrive. *Should* is the reason it is kept: an inbox reached before it
    was bound is precisely how a forged commitment once became the head of this
    queue, and the evidence of an attempt is worth more than the silence of a
    consumer that quietly dropped it.
    """


_install_peer_mcppeer_1(globals())
_install_peer_mcppeer_2(globals())
