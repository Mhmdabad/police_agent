import json
from pathlib import Path
from typing import Any
import pytest
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.domain.lock import ScentAgreement, ScentLock, propose
from cop_agent.domain.outcome import TechnicalLoss
from cop_agent.domain.scent import CHEBYSHEV
from cop_agent.domain.scoring import Outcome, scores_for
from cop_agent.infra.ceremony import AuditResult, Verdict
from cop_agent.infra.handshake import Greeting, Peering
from cop_agent.infra.inboxes import RETRY_KEY, PeerInboxes
from cop_agent.infra.match_log import MatchLog
from cop_agent.infra.mcp_client import ClientSettings, OpponentClient
from cop_agent.infra.report import Report, SubGameResult
from cop_agent.runtime.driver import (
    StartupTimeout,
    _cell,
    _now,
    _them,
    _us,
    await_opponent,
)
from cop_agent.runtime.match import MatchRunner, SubGameOutcome
from cop_agent.runtime.orchestrator import PROTOCOL_VERSION, MatchAborted, Orchestrator
from cop_agent.runtime.subgame import Played, SubGame
from cop_agent.shared.config import config_sha256
from cop_agent.strategy.police_brain import PoliceBrain
from test_localhost_match import REPOS, build_declaration, parameters  # noqa: E402
REPO = Path(__file__).resolve().parent.parent
WHEN = "2026-08-05T12:00:00+00:00"
AXES = AxisConvention()
class Answering:
    def __init__(self, reply: dict[str, Any]) -> None:
        self.reply = reply
        self.calls: list[tuple[str, dict[str, Any]]] = []
    def call(self, url: str, tool: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        self.calls.append((tool, payload))
        return self.reply
class Watching:
    def __init__(self) -> None:
        self.inboxes = PeerInboxes()
        self.bound: list[tuple[str, int]] = []
    def call(self, url: str, tool: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        self.bound.append((self.inboxes.game_uid, self.inboxes.sub_game))
        return {"ok": True}
def a_peering(role: str = "police", sub_game: int = 1) -> Peering:
    opponent = "thief" if role == "police" else "police"
    return Peering(
        ours=Greeting(
            role=role,
            group_id="s82kma9e",
            public_url="https://ours.ngrok.io",
            protocol_version=PROTOCOL_VERSION,
        ),
        theirs=Greeting(
            role=opponent,
            group_id="them",
            public_url="https://theirs.ngrok.io",
            protocol_version=PROTOCOL_VERSION,
        ),
        sub_game=sub_game,
    )
def stub_boundaries(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    crossed: list[int] = []
    def crossing(self: MatchRunner, number: int, timeout: float = 30.0) -> Peering:
        crossed.append(number)
        self.peering = a_peering(self.role, number)
        return self.peering
    monkeypatch.setattr(MatchRunner, "rehandshake", crossing)
    return crossed
def a_runner(
    tmp_path: Path, reply: dict[str, Any] | None = None, transport: Answering | None = None
) -> MatchRunner:
    transport = transport or Answering(reply if reply is not None else {"ok": True})
    return MatchRunner(
        orchestrator=Orchestrator(
            inboxes=PeerInboxes(),
            client=OpponentClient(
                transport=transport,
                settings=ClientSettings(opponent_url="http://127.0.0.1:1/mcp"),
            ),
            role="police",
        ),
        declaration=build_declaration("police", "uoh26-s82kma9e", "u-0001"),
        parameters=parameters(),
        brain=PoliceBrain(),
        axes=AXES,
        start=BoardState(grid_size=8, cop=(0, 0), thief=(6, 5), barriers=frozenset(), step=0),
        max_steps=2,
        directory=tmp_path,
        now=lambda: WHEN,
        peering=a_peering(),
    )
def an_outcome(number: int, clean: bool = True, captured: bool = False) -> SubGameOutcome:
    log = MatchLog(
        game_id="uoh26-s82kma9e",
        sub_game=number,
        role="police",
        game_uid="u-0001",
        config_sha256="c" * 64,
    )
    audit = (
        AuditResult(verdict=Verdict.CLEAN, checked=2)
        if clean
        else AuditResult(
            verdict=Verdict.FORGED,
            checked=2,
            failures=("step 2: committed abc… but the revealed move produces def…",),
        )
    )
    board = BoardState(grid_size=8, cop=(0, 0), thief=(6, 5), barriers=frozenset(), step=2)
    return SubGameOutcome(
        number=number,
        played=Played(2, board, captured, "capture" if captured else "step limit reached", audit),
        audit=audit,
        log=log,
    )
def answered(
    runner: MatchRunner, digest: str | None = None, lock: ScentLock | None = None
) -> MatchRunner:
    runner.orchestrator.inboxes.negotiate(
        {
            "config_sha256": digest if digest is not None else config_sha256(runner.parameters),
            "game_uid": runner.declaration.game_uid,
        }
    )
    runner.orchestrator.inboxes.negotiate(
        Orchestrator.scent_offer(lock or propose(), runner.declaration.game_uid)
    )
    return runner
def result_for_two() -> Report:
    return Report(
        game_id="uoh26-s82kma9e",
        game_uid="u-0001",
        role="police",
        team="uoh26-cops",
        opponent_team="uoh26-others",
        repositories=REPOS,
        sub_games=tuple(
            SubGameResult(sub_game=n, cop_score=0, thief_score=0, commit_hash=f"{n:040x}")
            for n in (1, 2)
        ),
        total_tokens=0,
        agreed=True,
    )
