"""Commit-Reveal sealing, in the wire form the cohort uses.

SHA256(canonical_bytes(payload | nonce)) commitment verification and audit.
"""

import hashlib
import secrets
from typing import Any

from ..shared.config import canonical_bytes
from .actions import ROLES
from .board import BoardState, Position

NONCE_BYTES = 16
"""Matches the reference. ``secrets.token_hex(16)`` gives a 32-char nonce."""


class CryptoError(ValueError):
    """Raised when a revealed record does not match its commitment."""


def nonce() -> str:
    """A fresh 128-bit nonce, from the CSPRNG and never from :mod:`random`."""
    return secrets.token_hex(NONCE_BYTES)


def canonical(payload: dict[str, Any]) -> str:
    """The canonical JSON text a commitment is taken over."""
    return canonical_bytes(payload).decode("utf-8")


def commit_of(payload: dict[str, Any], nonce: str) -> str:
    """The commitment for ``payload`` under ``nonce``."""
    if "nonce" in payload:
        raise CryptoError("payload already has a 'nonce'; pass it once, as the argument")
    return hashlib.sha256(canonical_bytes({**payload, "nonce": nonce})).hexdigest()


def board_terms(state: BoardState, role: str) -> dict[str, Any]:
    """The part of the board the opponent can check at the audit.

    Anti-replay is what the rulebook asks ``State`` for: it pins a commitment
    to one specific step so an old one cannot be reused in a new context. Grid
    size, step number, our own cell and the barrier set do that, and every one
    of them is independently verifiable by the other side once the match ends.

    **Our belief about their position is deliberately absent.** Including it
    would look more complete and be strictly worse: neither peer can check the
    other's belief, so a sealed belief is a number we could have written after
    the fact. Sealing something unverifiable does not make it true, it only
    makes the audit unable to say anything about it.

    Positions become lists because that is what survives JSON. A tuple and a
    list serialise identically going out and come back as a list, so a peer
    that re-hashed a parsed record would get a different digest from one that
    hashed its own.
    """
    if role not in ROLES:
        raise CryptoError(f"role must be one of {sorted(ROLES)}, got {role!r}")
    mine = state.cop if role == "police" else state.thief
    return {
        "grid_size": state.grid_size,
        "step": state.step,
        "self": list(mine),
        "barriers": sorted(list(cell) for cell in state.barriers),
    }


def step_record(
    state: BoardState,
    role: str,
    move: str,
    intent: str,
    hint: str,
    barrier_placed: Position | None = None,
    scent: dict[str, float] | None = None,
    *,
    game_uid: str = "series-123",
    sub_game: int = 2,
) -> dict[str, Any]:
    """Everything one step commits to, before the nonce is folded in."""
    return {
        "game_uid": game_uid,
        "sub_game": sub_game,
        "state": board_terms(state, role),
        "role": role,
        "move": move,
        "intent": intent,
        "hint": hint,
        "barrier_placed": list(barrier_placed) if barrier_placed else None,
        "scent": dict(scent) if scent is not None else None,
    }


def seal(payload: dict[str, Any]) -> dict[str, str]:
    """Draw a fresh nonce and commit to ``payload``.

    Returns the nonce alongside the commit. Only the commit crosses the wire at
    commit time; the nonce is withheld until the final audit, so an opponent
    cannot reverse-engineer the record while the match is still running.
    """
    fresh = nonce()
    return {"nonce": fresh, "commit": commit_of(payload, fresh)}


def verify(payload: dict[str, Any], nonce: str, commit: str) -> None:
    """Re-derive the commitment and compare.

    Raises:
        CryptoError: on any mismatch. There is no near-miss — SHA-256 is
            sensitive to every bit, so a difference is proof of tampering and
            costs the responsible team the match.
    """
    actual = commit_of(payload, nonce)
    if not secrets.compare_digest(actual, commit):
        raise CryptoError(f"commit mismatch: declared {commit[:16]}…, recomputed {actual[:16]}…")


def audit(records: list[dict[str, Any]]) -> None:
    """Re-verify every revealed record.

    Raises:
        CryptoError: naming the first failing step, since the match is void
            from that point and the step number is what the two teams have to
            agree on when reconciling the result.
    """
    for index, record in enumerate(records):
        try:
            verify(record["payload"], record["nonce"], record["commit"])
        except KeyError as exc:
            raise CryptoError(f"record {index} is missing {exc.args[0]!r}") from exc
        except CryptoError as exc:
            step = record.get("payload", {}).get("step", index)
            raise CryptoError(f"tampering at step {step}: {exc}") from exc
