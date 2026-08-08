import hashlib
import hmac
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..shared.config import canonical_bytes
from ._step_zero_hw import (
    CPU_MAX_FREQ as CPU_MAX_FREQ,
)
from ._step_zero_hw import (
    GPU_ENV as GPU_ENV,
)
from ._step_zero_hw import (
    VRAM_ENV as VRAM_ENV,
)
from ._step_zero_hw import (
    Hardware as Hardware,
)
from ._step_zero_hw import (
    _cpu_max_mhz as _cpu_max_mhz,
    _positive_int as _positive_int,
    _ram_mb as _ram_mb,
    collect as collect,
)


@dataclass(frozen=True, slots=True)
class Provenance:
    code_version: str
    group_name: str
    sub_game: int
    github_commit: str | None
    dirty: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "code_version": self.code_version,
            "group_name": self.group_name,
            "sub_game": self.sub_game,
            "github_commit": self.github_commit,
            "working_tree_dirty": self.dirty,
        }

    @property
    def reproducible(self) -> bool:
        return self.github_commit is not None and not self.dirty

    def __str__(self) -> str:
        if self.reproducible and self.github_commit:
            return f"{self.group_name} sub-game {self.sub_game} at {self.github_commit[:12]}"
        reason = "uncommitted changes" if self.dirty else "no commit hash available"
        return (
            f"{self.group_name} sub-game {self.sub_game}: NOT REPRODUCIBLE ({reason}); "
            "the declared commit does not describe the code that ran"
        )


def _git(*args: str, repo: Path | None = None) -> str | None:
    try:
        done = subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["git", *args],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return done.stdout.strip()


def provenance(
    code_version: str,
    group_name: str,
    sub_game: int,
    repo: Path | None = None,
) -> Provenance:
    commit = _git("rev-parse", "HEAD", repo=repo)
    status = _git("status", "--porcelain", repo=repo)
    return Provenance(
        code_version=code_version,
        group_name=group_name,
        sub_game=sub_game,
        github_commit=commit,
        dirty=bool(status),
    )


SIGNING_KEY_ENV = "STEP0_SIGNING_KEY"
UNSIGNED = "unsigned"
"""What a declaration says when no key was available. Not an empty signature."""


@dataclass(frozen=True, slots=True)
class Declaration:
    hardware: Hardware
    provenance: Provenance
    signature: str

    @property
    def signed(self) -> bool:
        return self.signature != UNSIGNED

    def to_dict(self) -> dict[str, Any]:
        return {**statement(self.hardware, self.provenance), "signature": self.signature}


def statement(hardware: Hardware, provenance: Provenance) -> dict[str, Any]:
    return {"hardware": hardware.to_dict(), "provenance": provenance.to_dict()}


def sign(content: dict[str, Any], key: str | None) -> str:
    if not key:
        return UNSIGNED
    return hmac.new(key.encode("utf-8"), canonical_bytes(content), hashlib.sha256).hexdigest()


def declare(
    hardware: Hardware, provenance: Provenance, environ: dict[str, str] | None = None
) -> Declaration:
    source = os.environ if environ is None else environ
    content = statement(hardware, provenance)
    return Declaration(
        hardware=hardware,
        provenance=provenance,
        signature=sign(content, source.get(SIGNING_KEY_ENV)),
    )


def verify_signature(declared: dict[str, Any], key: str | None) -> bool:
    claimed = declared.get("signature")
    if not isinstance(claimed, str) or claimed == UNSIGNED:
        return False
    content = {name: declared.get(name) for name in ("hardware", "provenance")}
    return hmac.compare_digest(sign(content, key), claimed)
