import copy
import inspect
import json
from pathlib import Path
from typing import Any
import pytest
from cop_agent import __main__ as cli
from cop_agent.__main__ import CONFIG, StartupError, main, resolve_series_length
from cop_agent.runtime import driver
from cop_agent.runtime.driver import open_match
from cop_agent.runtime.match import MatchRunner
from cop_agent.shared.appendix_f import TABLE, Param, Status, book_int
from cop_agent.shared.config import (
    SERIES_KEY,
    SERIES_SECTION,
    SHARED_CONFIG,
    ConfigError,
    series_length,
    validate,
)
from cop_agent.shared.terms import to_terms
from test_localhost_match import REPOS, parameters
from test_match import a_runner, an_outcome, stub_boundaries
REPO = Path(__file__).resolve().parent.parent
BOOK_SERIES = 6
NO_TUNNEL: dict[str, str] = {}
PUBLIC = {"PUBLIC_URL": "https://abc.ngrok.io"}
def shipped() -> dict[str, Any]:
    return json.loads((REPO / "config/game.json").read_text())  # type: ignore[no-any-return]
