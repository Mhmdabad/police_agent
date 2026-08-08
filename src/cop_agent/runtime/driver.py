"""Assembling a match from config, and running it against a live opponent."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..domain.axes import AxisConvention
from ..domain.board import BoardState
from ..infra.declaration import Endpoints, build
from ..infra.inboxes import PeerInboxes
from ..infra.mcp_client import ClientSettings, OpponentClient
from ..infra.mcp_transport import FastMcpTransport
from ..infra.report import Repositories
from ..infra.step_zero import SIGNING_KEY_ENV, collect, provenance
from ..infra.tunnel import discover, rehearsal_url
from ..shared.config import SHARED_CONFIG
from ..shared.config import load as load_shared
from ..strategy.loader import load_brain
from ._driver_helpers import (
    DEFAULT_PATIENCE as DEFAULT_PATIENCE,
)
from ._driver_helpers import (
    StartupTimeout as StartupTimeout,
)
from ._driver_helpers import (
    _them as _them,
)
from ._driver_helpers import (
    _us as _us,
)
from ._driver_helpers import (
    await_opponent as await_opponent,
)
from .match import MatchRunner
from .orchestrator import Orchestrator

ROLE = "police"


def open_match(
    *,
    inboxes: PeerInboxes,
    private: dict[str, Any],
    environ: dict[str, str],
    game_id: str,
    directory: Path,
    rehearsal: bool = False,
) -> tuple[Path, ...]:  # pragma: no cover - the other side of this is another team
    """Run a whole match and write its evidence. Returns the files written."""
    parameters = load_shared(SHARED_CONFIG)
    network = private.get("network", {})
    transport = FastMcpTransport()
    client = OpponentClient(
        transport=transport, settings=ClientSettings.from_config(network, environ)
    )
    orchestrator = Orchestrator(inboxes=inboxes, client=client, role=ROLE)

    if rehearsal:
        address = rehearsal_url(environ, int(network.get("my_port", 8801)))
    else:
        endpoint = discover(environ)
        address = endpoint.url if endpoint else ""
    ours = orchestrator.greeting(address, str(private.get("game", {}).get("group_id", "")))
    directory.mkdir(parents=True, exist_ok=True)
    peering = await_opponent(orchestrator, ours, directory, game_id)

    us, them = _us(private), _them(private)
    hardware = collect(str(private.get("trash_talk", {}).get("model", "template")), environ)

    declaration = build(
        game_id=game_id,
        game_uid=game_id,
        role=ROLE,
        us=us,
        them=them,
        endpoints=Endpoints(ours=ours.public_url or "local", theirs=peering.theirs.public_url),
        hardware=hardware,
        provenance=provenance(
            code_version=str(private.get("version", "1.0")),
            group_name=us.name,
            sub_game=1,
        ),
        llm_model=hardware.llm_model,
        token_ceiling=int(
            parameters.get("network_and_league", {}).get("token_budget_per_series", 200_000)
        ),
        started_at=_now(),
        key=environ.get(SIGNING_KEY_ENV),
    )

    board = parameters.get("board_and_agents", {})
    runner = MatchRunner(
        orchestrator=orchestrator,
        declaration=declaration,
        parameters=parameters,
        brain=load_brain(private.get("strategy")),
        axes=AxisConvention(),
        start=BoardState(
            grid_size=int(board.get("grid_size", 8)),
            cop=_cell(board.get("cop_start"), (0, 0)),
            thief=_cell(board.get("thief_start"), (6, 5)),
            barriers=frozenset(),
            step=0,
        ),
        max_steps=int(parameters.get("movement_and_barriers", {}).get("max_moves", 40)),
        directory=directory,
        now=_now,
        peering=peering,
    )

    try:
        runner.agree()
        runner.play_series()
    finally:
        transport.close()

    if not runner.opponent_played_fairly:
        for failure in runner.failures():
            print(f"  AUDIT FAILURE: {failure}")

    return runner.write(
        runner.result(
            commit_hash=declaration.provenance.github_commit or "unknown",
            total_tokens=0,
            agreed=False,
            repositories=Repositories(
                cop_repo=us.cop_repo,
                thief_repo=us.thief_repo,
                opponent_cop_repo=them.cop_repo,
                opponent_thief_repo=them.thief_repo,
            ),
        )
    )


def _cell(value: object, fallback: tuple[int, int]) -> tuple[int, int]:
    """A start position from JSON, which has lists rather than tuples."""
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return (int(value[0]), int(value[1]))
    return fallback


def _now() -> str:
    """An ISO-8601 UTC timestamp, to the second."""
    return datetime.now(UTC).isoformat(timespec="seconds")


__all__ = ["open_match"]
