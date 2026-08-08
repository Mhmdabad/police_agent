import copy
import json
from pathlib import Path
from typing import Any
import pytest
from cop_agent.shared.appendix_f import TABLE, Status, book_int, book_value
from cop_agent.shared.config import (
    ConfigError,
    canonical_bytes,
    config_sha256,
    load,
    validate,
)
CONFIG_PATH = Path(__file__).parents[1] / "config/game.json"
def shipped() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text())  # type: ignore[no-any-return]
