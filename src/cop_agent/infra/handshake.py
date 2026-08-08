"""Trading addresses before the first move, and writing them down.

Two peers who have never met know one thing about each other: a URL. This
module is where that URL is exchanged, checked, and recorded in the pre-game
declaration — the file that fixes everything which does not change during a
match, so that afterwards there is no argument about who was supposed to be at
which address.

**Checking is the part that earns its keep.** :mod:`.tunnel` refuses to
*advertise* an address an opponent could not route to; this module refuses to
*accept* one. The asymmetry matters: a peer can only verify its own tunnel by
trusting itself, but the address it is handed is a claim by someone with no
obligation to be careful. A loopback URL accepted here means every call we make
goes to our own machine, the deadline expires, and the match ends in a
technical loss scoring **zero for both sides** — including the side that made
the mistake.

The rule for that check is not "always demand a public address". It is
symmetric, and it has to be: during local development both agents run on one
box against ``127.0.0.1``, which is explicitly permitted while coding. So the
condition is **we may not demand more reachability than we ourselves offer**.
A peer advertising a tunnel refuses a loopback opponent, because it genuinely
cannot reach one. A peer still on loopback accepts a loopback opponent, because
that is the local test loop working as intended — and if the opponent is public
while we are not, that is fine too: they can be reached, and our own exposure is
their problem to complain about, not ours to pre-empt.

The declaration is **merged, not overwritten**. It accumulates across stages —
hardware, model and token ceiling arrive later — and a stage that rewrote the
file wholesale would silently drop whatever a previous one had recorded.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..shared.naming import declaration_filename
from .protocol import ROLES
from .validation import require_mapping

ADDRESS_KEY = "mcp_addresses"
"""Where addresses live in the declaration. One key, so merging is unambiguous."""


from ._handshake_greeting import (
    Greeting as Greeting,
)
from ._handshake_greeting import (
    HandshakeError as HandshakeError,
)
from ._handshake_greeting import (
    Peering as Peering,
)
from ._handshake_greeting import (
    check as check,
)
from ._handshake_greeting import (
    check_rotation as check_rotation,
)


@dataclass
class AddressBook:
    """Both peers' MCP addresses, in the shape the declaration records them."""

    entries: dict[str, dict[str, Any]]

    @classmethod
    def of(cls, ours: Greeting, theirs: Greeting, sub_game: int = 1) -> "AddressBook":
        """Build from a checked pair. Keyed by role, which is unique by :func:`check`.

        ``since_sub_game`` is recorded so the declaration says *when* an address
        took effect. Without it a rotated series looks, at audit, exactly like
        one that used the final address from the start.
        """
        return cls(
            {
                g.role: {**g.to_dict(), "reachable": g.reachable, "since_sub_game": sub_game}
                for g in (ours, theirs)
            }
        )

    @classmethod
    def peered(cls, peering: "Peering") -> "AddressBook":
        """Build from a :class:`Peering`, carrying its sub-game number through."""
        return cls.of(peering.ours, peering.theirs, peering.sub_game)

    @property
    def complete(self) -> bool:
        """Whether both roles are present. A one-sided book is not a match."""
        return set(self.entries) == set(ROLES)

    def to_fragment(self) -> dict[str, Any]:
        """The declaration entry this stage contributes."""
        return {ADDRESS_KEY: {role: dict(entry) for role, entry in sorted(self.entries.items())}}


def record(directory: Path, game_id: str, book: AddressBook) -> Path:
    """Merge the addresses into ``declaration_<game_id>.json``.

    Merged rather than written, because the declaration accumulates across
    stages: hardware statements, the model in use and the token ceiling arrive
    later, and a stage that rewrote the file would drop them without a trace.

    Raises:
        HandshakeError: if the book is one-sided. A declaration naming a single
            peer is evidence of nothing.
    """
    if not book.complete:
        raise HandshakeError(
            f"declaration needs both roles, have {sorted(book.entries)}; "
            "a one-sided address record proves nothing at audit"
        )
    path = directory / declaration_filename(game_id)
    existing: dict[str, Any] = {}
    if path.exists():
        loaded = json.loads(path.read_text())
        existing = require_mapping(loaded, "declaration")
    directory.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({**existing, **book.to_fragment()}, indent=2, sort_keys=True) + "\n")
    return path
