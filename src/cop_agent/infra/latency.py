"""How long the tunnel actually takes, and what that says about the timeouts."""

import math
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .mcp_client import Transport

DEFAULT_RESPONSE_TIMEOUT_SEC = 30.0
"""Appendix F. Negotiable **upward**: a minimum may be raised, never lowered."""

COMFORTABLE_HEADROOM = 10.0
"""Ratio of timeout to observed p95 below which the margin is worth reporting.

Ten rather than two. The failure this guards against is not the average call
being slow — it is one call in a match hitting a stall an order of magnitude
past normal, and a technical loss scores zero for **both** sides, so the cost
of a thin margin is a whole sub-game rather than a retry.
"""


@dataclass
class LatencyLog:
    """Observed round-trip times, in seconds, in the order they happened."""

    samples: list[float] = field(default_factory=list)
    by_tool: dict[str, list[float]] = field(default_factory=dict)

    def record(self, tool: str, seconds: float) -> None:
        """Add one observation. Negative durations are a broken clock, not data."""
        if seconds < 0:
            raise ValueError(f"round trip cannot be negative, got {seconds}")
        self.samples.append(seconds)
        self.by_tool.setdefault(tool, []).append(seconds)

    def summary(self) -> "Summary":
        return Summary.of(self.samples)


@dataclass(frozen=True, slots=True)
class Summary:
    """What a set of round trips looked like."""

    count: int
    fastest: float
    median: float
    p95: float
    slowest: float

    @classmethod
    def of(cls, samples: list[float]) -> "Summary":
        """Summarise, or report zeroes for an empty log."""
        if not samples:
            return cls(0, 0.0, 0.0, 0.0, 0.0)
        ordered = sorted(samples)
        return cls(
            count=len(ordered),
            fastest=ordered[0],
            median=percentile(ordered, 50),
            p95=percentile(ordered, 95),
            slowest=ordered[-1],
        )

    def __str__(self) -> str:
        if not self.count:
            return "no round trips measured yet"
        return (
            f"{self.count} round trips: fastest {self.fastest * 1000:.0f}ms, "
            f"median {self.median * 1000:.0f}ms, p95 {self.p95 * 1000:.0f}ms, "
            f"slowest {self.slowest * 1000:.0f}ms"
        )


def percentile(ordered: list[float], which: int) -> float:
    """Nearest-rank percentile of an already-sorted list."""
    if not ordered:
        return 0.0
    rank = max(1, math.ceil(which / 100 * len(ordered)))
    return ordered[min(rank, len(ordered)) - 1]


@dataclass(frozen=True, slots=True)
class Justification:
    """Whether the configured timeout is defensible against what we measured."""

    summary: Summary
    timeout_sec: float

    @property
    def headroom(self) -> float:
        """How many times the observed p95 fits into the timeout."""
        return math.inf if self.summary.p95 <= 0 else self.timeout_sec / self.summary.p95

    @property
    def measured(self) -> bool:
        """Whether there is any evidence at all behind the number."""
        return self.summary.count > 0

    @property
    def sufficient(self) -> bool:
        """Measured, and with an order of magnitude to spare."""
        return self.measured and self.headroom >= COMFORTABLE_HEADROOM

    def __str__(self) -> str:
        if not self.measured:
            return (
                f"response_timeout_sec = {self.timeout_sec:g}s is UNJUSTIFIED: "
                "no round trips have been measured over the tunnel yet"
            )
        verdict = "ample" if self.sufficient else "THIN"
        margin = "inf" if math.isinf(self.headroom) else f"{self.headroom:.0f}x"
        return (
            f"response_timeout_sec = {self.timeout_sec:g}s against {self.summary}; "
            f"margin over p95 is {margin} — {verdict}. The timeout covers a push "
            "and an enqueue only; the opponent's thinking is bounded separately "
            "by turn_timeout_seconds, because inbound calls are fire-and-forget."
        )


def justify(log: LatencyLog, timeout_sec: float = DEFAULT_RESPONSE_TIMEOUT_SEC) -> Justification:
    """State, in writing, whether the timeout survives what we observed."""
    return Justification(log.summary(), timeout_sec)


class TimedTransport:
    """Wraps a transport and times every call."""

    def __init__(
        self,
        inner: Transport,
        log: LatencyLog | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.inner = inner
        self.log = log if log is not None else LatencyLog()
        self._clock = clock

    def call(self, url: str, tool: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        """Time one call."""
        started = self._clock()
        result: dict[str, Any] = self.inner.call(url, tool, payload, timeout)
        self.log.record(tool, self._clock() - started)
        return result
