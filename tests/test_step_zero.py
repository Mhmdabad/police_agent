import ast
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any
import pytest
from cop_agent.infra.step_zero import (
    GPU_ENV,
    SIGNING_KEY_ENV,
    UNSIGNED,
    VRAM_ENV,
    Declaration,
    Hardware,
    _cpu_max_mhz,
    _positive_int,
    _ram_mb,
    collect,
    declare,
    provenance,
    sign,
    statement,
    verify_signature,
)
from cop_agent.shared.config import canonical_bytes
def repo(tmp_path: Path, commit: bool = True, dirty: bool = False) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True)
    (tmp_path / "agent.py").write_text("print('hello')\n")
    if commit:
        subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
        subprocess.run(["git", "commit", "-qm", "first"], cwd=tmp_path, check=True)
    if dirty:
        (tmp_path / "agent.py").write_text("print('changed after the commit')\n")
    return tmp_path
KEY = "a-key-the-course-supplies"
def declaration(tmp_path: Path, key: str | None = KEY) -> Declaration:
    return declare(
        collect("claude-haiku-4-5", environ={}),
        provenance("0.1.0", "s82kma9e", 1, repo=repo(tmp_path)),
        environ={SIGNING_KEY_ENV: key} if key else {},
    )
