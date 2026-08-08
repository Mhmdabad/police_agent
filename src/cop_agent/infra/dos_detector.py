"""Gate three: recognising a bug, and locking the door on it.

Anomalous send pattern detection and circuit breaker disk lock.
"""

import json
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path

BURST_LIMIT = 5
"""Sends inside :data:`WINDOW_SEC` that count as a burst.

Above anything a real match produces — one report per game — and far below the
30/minute the token bucket would happily allow.
"""

WINDOW_SEC = 60.0
"""The burst window."""

METRONOME_RUN = 4
"""Consecutive intervals that must be near-identical to look mechanical."""

METRONOME_TOLERANCE = 0.05
"""Relative spread below which a run of intervals is machine-regular.

Five percent. Human-paced events do not land this evenly; a loop with a fixed
sleep does almost nothing else.
"""

LOCK_PATH_ENV = "GMAIL_LOCK_PATH"


class DosDetected(RuntimeError):
    """Raised when the pipeline is locked. Not retryable, by design."""


def lock_path(package: str, environ: "dict[str, str] | None" = None) -> Path:
    chosen = (environ if environ is not None else dict(os.environ)).get(LOCK_PATH_ENV)
    return Path(chosen) if chosen else Path(f".locked_{package.split('_')[0]}.json")


@dataclass
class Detector:
    """Watches the shape of recent sends and locks the pipeline on a bug."""

    path: Path
    now: Callable[[], float]
    burst_limit: int = BURST_LIMIT
    window_sec: float = WINDOW_SEC
    metronome_run: int = METRONOME_RUN
    tolerance: float = METRONOME_TOLERANCE
    history: int = 32
    recent: list[float] = field(default_factory=list, init=False)

    def _within_window(self, moment: float) -> list[float]:
        return [at for at in self.recent if moment - at <= self.window_sec]

    @property
    def locked(self) -> bool:
        return self.path.exists()

    def reason(self) -> str:
        """Why the lock was set, for whoever finds it. Empty when unlocked."""
        try:
            body = json.loads(self.path.read_text())
        except (OSError, json.JSONDecodeError):
            return "locked, but the reason could not be read"
        return str(body.get("reason", "")) if isinstance(body, dict) else ""

    def check(self) -> None:
        """Refuse if the pipeline is locked. Called before anything else."""
        if self.locked:
            raise DosDetected(
                f"the send pipeline is locked: {self.reason()}. Nothing goes out until "
                f"somebody looks at why and clears {self.path} deliberately. One report "
                "is worth less than the account"
            )

    def record(self) -> None:
        """Note that a send is happening, and lock if the pattern looks mechanical."""
        self.check()
        moment = self.now()
        self.recent.append(moment)
        self.recent = self.recent[-self.history :]

        inside = self._within_window(moment)
        if len(inside) > self.burst_limit:
            self._lock(
                f"{len(inside)} sends within {self.window_sec:g}s, over the burst "
                f"limit of {self.burst_limit}"
            )
        spread = self._metronome()
        if spread is not None:
            self._lock(
                f"{self.metronome_run + 1} sends spaced {spread:g}s apart to within "
                f"{self.tolerance:.0%} — that is a loop's cadence, not a match's"
            )

    def _metronome(self) -> float | None:
        """The mean interval, if the last run of them is suspiciously even.

        Returns ``None`` when there is not enough history or the spacing is
        irregular — which is what real activity looks like. Intervals of zero
        are treated as mechanical too: nothing human sends twice in the same
        instant.
        """
        needed = self.metronome_run + 1
        if len(self.recent) < needed:
            return None
        tail = self.recent[-needed:]
        gaps = [later - earlier for earlier, later in pairwise(tail)]
        mean = sum(gaps) / len(gaps)
        if mean <= 0:
            return 0.0
        if max(abs(gap - mean) for gap in gaps) / mean > self.tolerance:
            return None
        return mean

    def _lock(self, reason: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(handle, "w") as stream:
            json.dump({"reason": reason, "at": self.now()}, stream, sort_keys=True)
            stream.write("\n")
        raise DosDetected(
            f"send pipeline locked — {reason}. This is the circuit breaker: one report "
            f"is sacrificed to save the account. Investigate, then delete {self.path}"
        )

    def reset(self) -> None:
        """Clear the lock. Deliberate, and never done by a failure path."""
        self.path.unlink(missing_ok=True)
        self.recent.clear()
