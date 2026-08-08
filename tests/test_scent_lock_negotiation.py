import json
import re
import threading
from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any
import pytest
from cop_agent.domain.fixture import BINDING
from cop_agent.domain.lock import ScentAgreement, propose, restate
from cop_agent.domain.outcome import TechnicalLoss
from cop_agent.domain.scent import CHEBYSHEV
from cop_agent.infra.ceremony import AuditResult, Verdict
from cop_agent.infra.inboxes import SCENT_DIGEST_KEY, SCENT_KEY, SERIES_KEY
from cop_agent.infra.mcp_server import ServerSettings, build, serve
from cop_agent.runtime.orchestrator import MatchAborted
from cop_agent.runtime.subgame import Played, SubGame
from cop_agent.shared.config import config_sha256
from test_config_agreement import (  # noqa: E402
    BRIEF,
    GAME_UID,
    OTHER_UID,
    OUR_ROLE,
    PATIENCE,
    THEIR_ROLE,
    Side,
    a_runner,
    a_side,
    altered,
    concurrently,
    fresh,
)
from test_localhost_match import free_port, parameters, wait_for  # noqa: E402
from test_match import stub_boundaries  # noqa: E402
@pytest.fixture(scope="module")
def wire() -> Iterator[tuple[Side, Side]]:
    our_port, their_port = free_port(), free_port()
    ours, theirs = a_side(OUR_ROLE, their_port), a_side(THEIR_ROLE, our_port)
    for side, port in ((ours, our_port), (theirs, their_port)):
        host = build(side.inboxes, name=f"{side.role}-scent-lock")
        threading.Thread(
            target=serve,
            args=(host, ServerSettings(port=port, host="127.0.0.1")),
            daemon=True,
        ).start()
        wait_for(port)
    yield ours, theirs
def our_lock() -> ScentAgreement:
    return propose().agreement()
def an_offer(
    changes: dict[str, Any] | None = None,
    *,
    uid: str | None = GAME_UID,
    digest: str | None = None,
    drop: str | None = None,
) -> dict[str, Any]:
    terms = propose().terms()
    model = terms["scent_model"]
    assert isinstance(model, dict)
    if drop is not None:
        del model[drop]
    model.update(changes or {})
    body: dict[str, Any] = {SCENT_KEY: terms, SCENT_DIGEST_KEY: digest or restate(terms)}
    if uid is not None:
        body[SERIES_KEY] = uid
    return body
def finer_precision() -> dict[str, Any]:
    emission = propose().fixture.as_terms()["emission"]
    assert isinstance(emission, dict)
    return {"emission": {cell: value + 1e-9 for cell, value in emission.items()}}
DIVERGENCES: dict[str, dict[str, Any]] = {
    "emission-radius": {"grid_size": 7},
    "kernel": {"model": "chebyshev"},
    "intensities": {"emission": {"2,2": 0.9}},
    "centre-intensity": {"centre_intensity": 0.8},
    "decay-rate": {"decay_rate": 0.2},
    "decay-rule": {"decay_series": [0.80, 0.70, 0.60]},
    "board-size": {"board_size": 8},
    "binding": {"binding": "turn-message-unbound"},
}
"""One divergence per term the lock exists to settle, each fatal on its own."""
def lock_gate(side: Side, timeout: float = PATIENCE) -> Callable[[], ScentAgreement]:
    return lambda: side.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=timeout)
def both_lock(wire: tuple[Side, Side], timeout: float = PATIENCE) -> dict[str, Any]:
    ours, theirs = fresh(wire)
    return concurrently({"ours": lock_gate(ours, timeout), "theirs": lock_gate(theirs, timeout)})
