import argparse
import json
import sys
import tomllib
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any
from .infra.inboxes import TOOL_NAMES, PeerInboxes
from .infra.mcp_client import ClientSettings
from .infra.mcp_server import SERVER_NAME, ServerSettings, build, serve
from .infra.tunnel import NotPublicError, discover, read_ngrok_api
from .shared.config import SHARED_CONFIG, series_length
from .shared.config import load as load_shared
PACKAGE = "cop_agent"
ROLE = "police"
CONFIG = Path("config/police/game.toml")
_DEFAULT: Any = object()
class StartupError(RuntimeError):
    pass
def load_private(path: Path) -> dict[str, Any]:
    try:
        body: dict[str, Any] = tomllib.loads(path.read_text())
    except FileNotFoundError as exc:
        raise StartupError(
            f"no private config at {path}; it is committed to this repository, so a "
            "missing one means the command is being run from somewhere other than the "
            "repository root"
        ) from exc
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise StartupError(f"cannot read {path}: {exc}") from exc
    return body
def resolve_series_length(requested: int | None, path: Path) -> int:
    try:
        config = load_shared(path)
    except OSError as exc:
        raise StartupError(
            f"cannot read the shared configuration at {path}: {exc}; it is committed to "
            "this repository, so a missing one means the command is being run from "
            "somewhere other than the repository root"
        ) from exc
    except json.JSONDecodeError as exc:
        raise StartupError(f"{path} is not valid JSON: {exc}") from exc
    return series_length(config, requested)
def where_we_are(
    environ: dict[str, str], reader: Callable[[], str | bytes] | None = _DEFAULT
) -> str:
    try:
        endpoint = discover(environ, read_ngrok_api if reader is _DEFAULT else reader)
    except NotPublicError as exc:
        raise StartupError(f"the address we would advertise is unusable: {exc}") from exc
    if endpoint is None:
        return "not publicly reachable — fine for local play, not for a league match"
    return endpoint.url
def describe(private: dict[str, Any], environ: dict[str, str]) -> list[str]:
    network = private.get("network", {})
    server = ServerSettings.from_config(network)
    client = ClientSettings.from_config(network, environ)
    return [
        f"{SERVER_NAME} ({ROLE})",
        f"  listening on   {server.host}:{server.port} ({server.transport})",
        f"  reachable at   {where_we_are(environ)}",
        f"  opponent at    {client.opponent_url}",
        f"  tools          {', '.join(sorted(TOOL_NAMES))}",
    ]
def main(argv: Sequence[str] | None = None, environ: dict[str, str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=f"python -m {PACKAGE}", description=__doc__)
    parser.add_argument(
        "command",
        nargs="?",
        default="serve",
        choices=("serve", "check", "play"),
        help=(
            "serve: run the peer and answer. check: report the configuration and exit. "
            "play: serve and open a match against an opponent who has already started."
        ),
    )
    parser.add_argument("--config", type=Path, default=CONFIG, help="private per-peer TOML")
    parser.add_argument("--game-id", default="", help="agreed with the opponent beforehand")
    parser.add_argument("--out", type=Path, default=Path("artefacts"), help="where to write")
    parser.add_argument(
        "--sub-games",
        type=int,
        default=None,
        help="sub-games in the series. Appendix F table 18 row 1 fixes this at six and "
        "deviating disqualifies the team, so the length comes from the shared config; "
        "the flag exists only so that asking for another is refused out loud",
    )
    parser.add_argument(
        "--rehearse",
        action="store_true",
        help="play this project's other agent over loopback, no tunnel — practice only, "
        "never against another team",
    )
    arguments = parser.parse_args(argv)
    import os  # noqa: PLC0415 - read once, here, so tests can supply their own
    source = dict(os.environ) if environ is None else environ
    try:
        private = load_private(arguments.config)
        for line in describe(private, source):
            print(line)
        sub_games = resolve_series_length(arguments.sub_games, SHARED_CONFIG)
        print(f"  series         {sub_games} sub-games (Appendix F table 18 row 1, fixed)")
        if arguments.command == "check":
            return 0
        settings = ServerSettings.from_config(private.get("network", {}))
        if arguments.command == "play":
            require_playable(arguments, source)
    except (StartupError, ValueError) as exc:
        print(f"cannot start: {exc}", file=sys.stderr)
        return 1
    inboxes = PeerInboxes()
    if arguments.command == "play":
        return play(arguments, private, settings, inboxes, source)
    print("serving — stop with Ctrl-C", flush=True)
    serve(build(inboxes), settings)
    return 0
def require_playable(
    arguments: argparse.Namespace,
    environ: dict[str, str],
    reader: Callable[[], str | bytes] | None = _DEFAULT,
) -> None:
    if not arguments.game_id:
        raise StartupError(
            "play needs --game-id, agreed with the opponent before either side "
            "starts; both sides' files are named from it and must match"
        )
    if getattr(arguments, "rehearse", False):
        return
    probe = read_ngrok_api if reader is _DEFAULT else reader
    if discover(environ, probe) is None:
        raise StartupError(
            "no public address to announce. Start a tunnel and export PUBLIC_URL, "
            "because announcing a loopback address to another team means every call "
            "they make times out — and a technical loss scores zero for both sides, "
            "not just for us. Use `check` to confirm before you try again"
        )
from ._main_commands import (
    _install as _install_main_commands,
)
from ._main_commands import (
    MAX_DEPTH,
    describe_failure,
    play,
    safely_describe,
)
_install_main_commands(globals())
if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
