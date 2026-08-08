"""Loading and validating the shared game configuration.

The shared ``game.json`` is the constitution both peers sign. It is loaded
byte-identically on each side and its SHA-256 is exchanged before the first
move; any mismatch means refuse to play.
"""

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any, Final

from .appendix_f import TABLE, Param, Status, book_int

SHARED_CONFIG = Path("config/game.json")
"""Where the agreed configuration lives, relative to the repository root.

One constant rather than one per caller: two paths to the constitution is two
constitutions, and the second one is the one nobody validates.
"""

SERIES_SECTION: Final = "network_and_league"
SERIES_KEY: Final = "num_games"
"""Appendix F table 18 row 1 — how many sub-games one series against an opponent is."""


class ConfigError(ValueError):
    """Raised when a configuration violates Appendix F."""


def _wrong_type(actual: object, expected: object) -> bool:
    """Whether a value deviates in *type*, before its value is even compared.

    ``6.0 == 6`` and ``True == 1`` in Python, so equality alone lets a float or
    a boolean stand in for a fixed integer. That is not a pedantic distinction
    here: ``"num_games": true`` compares equal to nothing the book says, but
    ``range(1, True + 1)`` plays one sub-game, and a config that validates while
    the series runs short is exactly the deviation this module exists to catch —
    found at audit, by the opponent, after the match.

    Applied to fixed parameters only. A minimum is compared with ``<``, which
    already refuses the shapes it cannot order.
    """
    if isinstance(expected, bool) or isinstance(actual, bool):
        return not (isinstance(expected, bool) and isinstance(actual, bool))
    if isinstance(expected, int):
        return not isinstance(actual, int)
    if isinstance(expected, float):
        return not isinstance(actual, int | float)
    return not isinstance(actual, type(expected))


def _violation(param: Param, actual: object) -> str | None:
    if param.status is Status.FIXED and (
        _wrong_type(actual, param.book_value) or actual != param.book_value
    ):
        return (
            f"{param.section}.{param.key} = {actual!r} but Appendix F fixes "
            f"{param.book_value!r}; deviating from a fixed value disqualifies the team"
        )
    if (
        param.status is Status.MINIMUM
        and isinstance(actual, int | float)
        and isinstance(param.book_value, int | float)
        and actual < param.book_value
    ):
        return (
            f"{param.section}.{param.key} = {actual!r} is below the Appendix F "
            f"minimum {param.book_value!r}; minimums may be raised, never lowered"
        )
    return None


def validate(config: dict[str, Any]) -> None:
    """Check every parameter against Appendix F.

    Raises:
        ConfigError: listing every violation found, not merely the first, so a
            misconfigured file is fixed in one pass rather than several.
    """
    problems: list[str] = []
    for param in TABLE:
        section = config.get(param.section)
        if not isinstance(section, dict) or param.key not in section:
            problems.append(f"{param.section}.{param.key} is missing")
            continue
        problem = _violation(param, section[param.key])
        if problem:
            problems.append(problem)
    if problems:
        raise ConfigError("; ".join(problems))


def series_length(config: dict[str, Any], requested: int | None = None) -> int:
    """How many sub-games one series against an opponent is."""
    validate(config)
    length = book_int(SERIES_SECTION, SERIES_KEY)
    if requested is not None and requested != length:
        raise ConfigError(
            f"a series length of {requested} was asked for, but Appendix F table 18 row 1 "
            f"fixes a series at {length} sub-games; deviating from a fixed value "
            "disqualifies the team"
        )
    return length


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    """The one canonical form. Every digest in this system is taken over it."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def config_sha256(config: dict[str, Any]) -> str:
    """The digest exchanged before the first move."""
    return hashlib.sha256(canonical_bytes(config)).hexdigest()


def digests_agree(ours: str, theirs: str) -> bool:
    """Whether two peers are playing by the same parameters.

    Constant-time, via :func:`hmac.compare_digest`. Not because a config digest
    is a secret — both sides publish theirs — but because ``==`` on strings
    stops at the first differing byte, and the time it takes therefore says how
    long a common prefix was. An opponent free to re-negotiate could use that to
    walk a digest out of us one character at a time and then claim our
    parameters as its own. The comparison costs nothing either way, and the
    version that leaks is the one that has to be justified.

    Compared as bytes rather than as ``str``: ``compare_digest`` raises
    ``TypeError`` on a non-ASCII string, and an unhandled exception on a path an
    opponent can reach is a technical loss scoring zero for both sides.
    """
    return hmac.compare_digest(ours.encode("utf-8"), theirs.encode("utf-8"))


def load(path: Path) -> dict[str, Any]:
    """Read and validate a shared configuration file."""
    config: dict[str, Any] = json.loads(path.read_text())
    validate(config)
    return config
