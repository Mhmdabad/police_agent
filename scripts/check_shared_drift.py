from __future__ import annotations
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
SIBLING_URL = "https://github.com/Mhmdabad/theif_agent"
SIBLING_PACKAGE = "thief_agent"
OUR_PACKAGE = "cop_agent"
SHARED: tuple[str, ...] = (
    "domain/axes.py",
    "domain/board.py",
    "domain/crypto.py",
    "domain/rules.py",
    "domain/search.py",
    "domain/actions.py",
    "domain/scoring.py",
    "domain/scent.py",
    "domain/scent_audit.py",
    "domain/trail.py",
    "domain/memory.py",
    "domain/fixture.py",
    "domain/lock.py",
    "domain/belief.py",
    "domain/inference.py",
    "domain/credibility.py",
    "domain/foci.py",
    "domain/hints.py",
    "domain/bluff.py",
    "domain/providers.py",
    "domain/budgeting.py",
    "infra/artefacts.py",
    "infra/ceremony.py",
    "runtime/match.py",
    "runtime/peer.py",
    "runtime/subgame.py",
    "infra/mcp_transport.py",
    "infra/config_file.py",
    "infra/credentials.py",
    "infra/declaration.py",
    "infra/dos_detector.py",
    "infra/gatekeeper.py",
    "infra/mailer.py",
    "infra/quota.py",
    "infra/report.py",
    "infra/token_bucket.py",
    "infra/token_store.py",
    "infra/gmail_auth.py",
    "infra/handshake.py",
    "infra/inboxes.py",
    "infra/latency.py",
    "infra/tunnel.py",
    "infra/match_log.py",
    "infra/mcp_client.py",
    "infra/mcp_server.py",
    "infra/protocol.py",
    "infra/step_zero.py",
    "infra/transport_log.py",
    "infra/token_ledger.py",
    "infra/validation.py",
    "runtime/deadline.py",
    "runtime/scheduler.py",
    "runtime/state_machine.py",
    "runtime/watchdog.py",
    "ui/banner.py",
    "ui/app.py",
    "ui/paint.py",
    "ui/replay.py",
    "ui/verdict.py",
    "ui/view.py",
    "shared/appendix_f.py",
    "shared/config.py",
    "shared/naming.py",
    "shared/terms.py",
)
"""Modules that must be identical once the package name is normalised."""
DIVERGENT: dict[str, str] = {
    "runtime/driver.py": "names this role and its private config path",
    "__main__.py": "names this role, its private config path and its default port",
    "infra/authorize.py": "stamps the role into the token; both agents share one OAuth client",
    "__init__.py": "package docstring names the role this repo implements",
    "domain/outcome.py": "capture-claim framing differs: who is obliged, and to whom",
    "runtime/orchestrator.py": "role default, and the duplicate-role failure differs by side",
    "strategy/base.py": "notes which hooks this role overrides",
    "strategy/loader.py": "reads police_class vs thief_class",
    "domain/barrier_audit.py": "cop-only; the thief has no barriers to replay",
    "strategy/barriers.py": "cop-only; the thief has no barriers to place",
    "strategy/budget.py": "cop-only; the thief has no quota to spend",
    "strategy/pursuit.py": "cop-only; only the cop re-aims a pursuit",
    "strategy/tradeoff.py": "cop-only; only the cop forfeits movement to place",
    "strategy/police_brain.py": "the cop's policy; no counterpart there",
    "strategy/thief_brain.py": "the thief's policy; no counterpart here",
}
"""Files that differ on purpose, each with the reason. Not a suppression list."""
_PACKAGE_RE = re.compile(rf"\b({SIBLING_PACKAGE}|{OUR_PACKAGE})\b")
def current_branch() -> str | None:
    for variable in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        name = os.environ.get(variable, "").strip()
        if name and name != "main":
            return name
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    name = result.stdout.strip()
    return name if name and name not in ("main", "HEAD") else None
def _try_clone(destination: Path, ref: str) -> bool:
    result = subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", ref, SIBLING_URL, str(destination)],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0
def clone_sibling(destination: Path, ref: str, prefer: str | None = None) -> tuple[Path, str]:
    if prefer and _try_clone(destination, prefer):
        return destination / "src" / SIBLING_PACKAGE, prefer
    subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", ref, SIBLING_URL, str(destination)],
        check=True,
        capture_output=True,
        text=True,
    )
    return destination / "src" / SIBLING_PACKAGE, ref
def compare(ours: Path, theirs: Path) -> list[str]:
    problems: list[str] = []
    for relative in SHARED:
        mine, sibling = ours / relative, theirs / relative
        if not mine.exists():
            problems.append(f"{relative}: missing here")
            continue
        if not sibling.exists():
            problems.append(f"{relative}: missing in the sibling repository")
            continue
        if normalise(mine.read_text()) != normalise(sibling.read_text()):
            problems.append(f"{relative}: drifted")
    return problems
from shared_drift_main import install, main
install(globals())
if __name__ == "__main__":
    raise SystemExit(main())
