#!/usr/bin/env python3
"""Fail if a maintained text file is longer than 149 lines."""

from __future__ import annotations

from pathlib import Path

MAX_LINES = 149
EXEMPT_FILES = {"uv.lock"}
EXEMPT_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}


def line_count(path: Path) -> int:
    """Physical lines, counted the way an editor shows them."""
    return len(path.read_text(encoding="utf-8").splitlines())


def main() -> int:
    over: list[tuple[int, str]] = []
    checked = 0
    for path in sorted(path for path in Path(".").rglob("*") if path.is_file()):
        if path.name in EXEMPT_FILES or any(part in EXEMPT_PARTS for part in path.parts):
            continue
        try:
            count = line_count(path)
        except UnicodeDecodeError:
            continue
        checked += 1
        if count > MAX_LINES:
            over.append((count, path.as_posix()))

    if over:
        print(f"{len(over)} module(s) over the {MAX_LINES}-line budget (split them):")
        for count, name in sorted(over, reverse=True):
            print(f"  {count:5d}  {name}")
        return 1
    print(f"{checked} maintained text files all within the {MAX_LINES}-line budget")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
