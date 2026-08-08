"""The match log: what happened, in the order it happened, never rewritten."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..domain.actions import ROLES
from ..shared.naming import log_filename

SLOTS = ("commit", "reveal", "nonce")


class MatchLogError(ValueError):
    """Raised on any attempt to write a slot that is already written."""


@dataclass(frozen=True, slots=True)
class Completeness:
    """Whether a log can be fully re-verified, and what is absent if not."""

    missing: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        return not self.missing

    def __str__(self) -> str:
        if self.complete:
            return "a third party can fully re-verify this sub-game"
        return "cannot be fully re-verified without " + "; ".join(self.missing)


@dataclass
class StepEntry:
    """One step's row. Each field is write-once."""

    step: int
    commit: str | None = None
    reveal: dict[str, Any] | None = None
    nonce: str | None = None
    discussion: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "commit": self.commit,
            "reveal": self.reveal,
            "nonce": self.nonce,
            "discussion": self.discussion,
        }


@dataclass
class MatchLog:
    """Every step of one sub-game, append-only."""

    game_id: str
    sub_game: int
    role: str
    game_uid: str = ""
    config_sha256: str = ""
    entries: dict[int, StepEntry] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise MatchLogError(f"role must be one of {sorted(ROLES)}, got {self.role!r}")
        log_filename(self.game_id, self.sub_game)  # validates both, raising NamingError

    def _slot(self, step: int, name: str) -> StepEntry:
        entry = self.entries.setdefault(step, StepEntry(step=step))
        if getattr(entry, name) is not None:
            raise MatchLogError(
                f"step {step} already has a {name}; this log is append-only, and a log "
                "that permitted an overwrite would be as convincing as no log at all"
            )
        return entry

    def commit(self, step: int, digest: str) -> None:
        """Record a commitment, before the move goes out."""
        self._slot(step, "commit").commit = digest

    def reveal(self, step: int, sealed: dict[str, Any]) -> None:
        """Record the **sealed record** — what the commitment was taken over."""
        entry = self._slot(step, "reveal")
        if entry.commit is None:
            raise MatchLogError(f"step {step} revealed with no commitment recorded")
        entry.reveal = sealed

    def disclose(self, step: int, nonce: str) -> None:
        """Record a nonce, once the match is over."""
        entry = self._slot(step, "nonce")
        if entry.reveal is None:
            raise MatchLogError(f"step {step} has no reveal to open")
        entry.nonce = nonce

    def discuss(self, step: int, fields: dict[str, Any]) -> None:
        """Record the LLM discussion fields for a step. Write-once, like the rest."""
        entry = self._slot(step, "discussion")
        if entry.commit is None:
            raise MatchLogError(f"step {step} has discussion recorded before any commitment")
        entry.discussion = fields

    def unopened(self) -> list[int]:
        """Steps with no nonce yet. Empty is the only acceptable end state."""
        return sorted(step for step, entry in self.entries.items() if entry.nonce is None)

    def verifiable(self) -> "Completeness":
        """Whether a third party could fully re-verify this sub-game from this file."""
        missing: list[str] = []
        if not self.game_uid:
            missing.append("game_uid (nothing ties this log to the declaration)")
        if not self.config_sha256:
            missing.append("config_sha256 (nobody can say which physics applied)")
        if not self.entries:
            missing.append("steps (a log of nothing verifies nothing)")
        unopened = self.unopened()
        if unopened:
            missing.append(f"nonces for steps {unopened}")
        unrevealed = sorted(step for step, entry in self.entries.items() if entry.reveal is None)
        if unrevealed:
            missing.append(f"reveals for steps {unrevealed}")
        return Completeness(tuple(missing))

    def to_dict(self) -> dict[str, Any]:
        """The file's contents, sorted by step so identical histories agree."""
        return {
            "game_id": self.game_id,
            "game_uid": self.game_uid,
            "sub_game": self.sub_game,
            "role": self.role,
            "config_sha256": self.config_sha256,
            "steps": [self.entries[step].to_dict() for step in sorted(self.entries)],
        }

    def write(self, directory: Path) -> Path:
        """Write ``log_<game_id>_g<NN>.json``, creating the directory if needed."""
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / log_filename(self.game_id, self.sub_game)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n")
        return path
