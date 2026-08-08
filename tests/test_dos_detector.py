import contextlib
import json
import stat
from pathlib import Path
import pytest
from cop_agent.infra.dos_detector import (
    BURST_LIMIT,
    LOCK_PATH_ENV,
    METRONOME_RUN,
    Detector,
    DosDetected,
    lock_path,
)
class Clock:
    def __init__(self, at: float = 1000.0) -> None:
        self.at = at
    def __call__(self) -> float:
        return self.at
    def advance(self, seconds: float) -> None:
        self.at += seconds
def detector(tmp_path: Path, clock: Clock | None = None) -> Detector:
    return Detector(path=tmp_path / ".locked_cop.json", now=clock or Clock())
def realistic(gate: Detector, clock: Clock, count: int = 10) -> None:
    for gap in ([600.0, 431.0, 907.0, 1200.0, 522.0] * 4)[:count]:
        clock.advance(gap)
        gate.record()
