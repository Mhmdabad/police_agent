"""Validating what arrives from the opponent.

Guards inbound payloads against malformed data, bad types, and illegal inputs.
"""

import math
import re
import unicodedata
from typing import Any

from ..domain.hints import FUTURE_ACTION, NUMERIC, policy_text

MAX_STRING = 4096
SHA256_HEX_CHARS = 64
_SHA256_HEX = re.compile(f"[0-9a-fA-F]{{{SHA256_HEX_CHARS}}}")
MAX_SCENT_CELLS = 10_000


class InvalidPayloadError(ValueError):
    """Raised when an inbound payload cannot be trusted."""


def require_mapping(payload: object, what: str = "payload") -> dict[str, Any]:
    """Accept only a JSON object."""
    if not isinstance(payload, dict):
        raise InvalidPayloadError(f"{what} must be an object, got {type(payload).__name__}")
    for key in payload:
        if not isinstance(key, str):
            raise InvalidPayloadError(f"{what} keys must be strings, got {type(key).__name__}")
    return payload


def require_str(payload: dict[str, Any], key: str, *, max_length: int = MAX_STRING) -> str:
    """A present, non-empty, length-bounded string."""
    if key not in payload:
        raise InvalidPayloadError(f"missing required field {key!r}")
    value = payload[key]
    if not isinstance(value, str):
        raise InvalidPayloadError(f"{key!r} must be a string, got {type(value).__name__}")
    if not value:
        raise InvalidPayloadError(f"{key!r} must not be empty")
    if len(value) > max_length:
        raise InvalidPayloadError(f"{key!r} exceeds {max_length} characters")
    return value


def require_hint(payload: dict[str, Any], key: str = "hint", *, max_words: int = 15) -> str:
    """A required, non-empty Unicode hint within the negotiated word cap."""
    value = require_str(payload, key)
    if not value.strip():
        raise InvalidPayloadError(f"{key!r} must not be blank")
    for character in value:
        category = unicodedata.category(character)
        if category == "Cs":
            raise InvalidPayloadError(f"{key!r} must contain Unicode scalar values")
        if category == "Cc":
            raise InvalidPayloadError(f"{key!r} contains a control character")
        if category == "Cf":
            raise InvalidPayloadError(f"{key!r} contains a Unicode format character")
    checked = policy_text(value)
    if NUMERIC.search(checked):
        raise InvalidPayloadError(f"{key!r} contains numeric coordinates")
    if FUTURE_ACTION.search(checked):
        raise InvalidPayloadError(f"{key!r} discloses a future action")
    count = len(value.split())
    if count > max_words:
        raise InvalidPayloadError(f"{key!r} has {count} words, over {max_words} words")
    return value


def require_digest(payload: dict[str, Any], key: str) -> str:
    """A SHA-256 digest, returned in the one spelling both peers hash to."""
    value = require_str(payload, key, max_length=SHA256_HEX_CHARS)
    if not _SHA256_HEX.fullmatch(value):
        raise InvalidPayloadError(
            f"{key!r} must be {SHA256_HEX_CHARS} hexadecimal characters, got {value!r}"
        )
    return value.lower()


def require_int(payload: dict[str, Any], key: str, *, minimum: int, maximum: int) -> int:
    """A present, in-range integer."""
    if key not in payload:
        raise InvalidPayloadError(f"missing required field {key!r}")
    value = payload[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidPayloadError(f"{key!r} must be an integer, got {type(value).__name__}")
    if not minimum <= value <= maximum:
        raise InvalidPayloadError(f"{key!r} must be {minimum}..{maximum}, got {value}")
    return value


def require_choice(payload: dict[str, Any], key: str, allowed: frozenset[str]) -> str:
    """A string field restricted to a known set."""
    value = require_str(payload, key)
    if value not in allowed:
        raise InvalidPayloadError(f"{key!r} must be one of {sorted(allowed)}, got {value!r}")
    return value


def reject_unknown_fields(payload: dict[str, Any], allowed: frozenset[str]) -> None:
    """Refuse fields we do not expect."""
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise InvalidPayloadError(f"unexpected fields: {unknown}")


def optional_scent(payload: dict[str, Any], key: str) -> dict[str, float] | None:
    """A ``{"row,col": intensity}`` field, or absent."""
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise InvalidPayloadError(f"{key!r} must be an object, got {type(value).__name__}")
    if len(value) > MAX_SCENT_CELLS:
        raise InvalidPayloadError(f"{key!r} names {len(value)} cells, over {MAX_SCENT_CELLS}")
    field: dict[str, float] = {}
    for cell, intensity in value.items():
        if not isinstance(cell, str):
            raise InvalidPayloadError(f"{key!r} keys must be strings, got {type(cell).__name__}")
        if isinstance(intensity, bool) or not isinstance(intensity, int | float):
            raise InvalidPayloadError(
                f"{key!r} intensity at {cell!r} must be a number, got {type(intensity).__name__}"
            )
        if not math.isfinite(intensity):
            raise InvalidPayloadError(f"{key!r} intensity at {cell!r} must be finite")
        if intensity < 0.0:
            raise InvalidPayloadError(f"{key!r} intensity at {cell!r} must not be negative")
        field[cell] = float(intensity)
    return field


def optional_cell(payload: dict[str, Any], key: str) -> list[int] | None:
    """A ``[row, col]`` pair, or absent."""
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != 2:
        raise InvalidPayloadError(f"{key!r} must be a [row, col] pair, got {value!r}")
    for element in value:
        if isinstance(element, bool) or not isinstance(element, int):
            raise InvalidPayloadError(f"{key!r} coordinates must be integers, got {value!r}")
    return [int(value[0]), int(value[1])]
