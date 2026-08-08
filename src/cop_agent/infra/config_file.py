"""``config_<game_id>_g<NN>.json`` — locked sub-game physics configuration."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..shared.config import ConfigError, config_sha256, validate
from ..shared.naming import config_filename


class ConfigFileError(ValueError):
    """Raised when a locked config cannot be built, read or trusted."""


@dataclass(frozen=True, slots=True)
class LockedConfig:
    """One sub-game's agreed parameters, with the digest that pins them."""

    game_id: str
    game_uid: str
    sub_game: int
    parameters: dict[str, Any]
    agreed_between: tuple[str, str]

    def __post_init__(self) -> None:
        if not self.game_uid:
            raise ConfigFileError("every artefact of a match shares a game_uid; this has none")
        if not self.parameters:
            raise ConfigFileError("a config with no parameters agrees to nothing")
        if len(set(self.agreed_between)) != 2:
            raise ConfigFileError(
                f"a config is agreed between two teams, got {self.agreed_between!r}"
            )
        config_filename(self.game_id, self.sub_game)  # validates both, raising NamingError

    @property
    def sha256(self) -> str:
        """The digest, over the parameters alone.

        Recomputed on every access rather than stored. A cached digest is a
        second copy of a fact that already exists, and the only way the two can
        differ is the way that matters.
        """
        return config_sha256(self.parameters)

    @property
    def filename(self) -> str:
        return config_filename(self.game_id, self.sub_game)

    def to_dict(self) -> dict[str, Any]:
        return {
            "game_id": self.game_id,
            "game_uid": self.game_uid,
            "sub_game": self.sub_game,
            "agreed_between": list(self.agreed_between),
            "parameters": self.parameters,
            "config_sha256": self.sha256,
        }

    def agrees_with(self, their_sha256: str) -> bool:
        """Whether the opponent's digest matches ours. #121 refuses play if not."""
        return self.sha256 == their_sha256

    def write(self, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / self.filename
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n")
        return path


def lock(
    *,
    game_id: str,
    game_uid: str,
    sub_game: int,
    parameters: dict[str, Any],
    agreed_between: tuple[str, str],
) -> LockedConfig:
    """Validate against Appendix F, then lock."""
    try:
        validate(parameters)
    except ConfigError as exc:
        raise ConfigFileError(
            f"refusing to lock a config that violates Appendix F: {exc}. A *fixed* "
            "parameter that deviates disqualifies the team, and a locked bad value "
            "is still a bad value"
        ) from exc
    return LockedConfig(
        game_id=game_id,
        game_uid=game_uid,
        sub_game=sub_game,
        parameters=parameters,
        agreed_between=agreed_between,
    )


def load(path: Path) -> LockedConfig:
    """Read a locked config, recomputing its digest rather than trusting it.

    Config files are committed to the repository, so they get opened, diffed
    and occasionally edited. A loader that believed the stored digest would let
    a hand edit travel under a hash that no longer describes it — which is the
    one thing the digest exists to prevent.

    Raises:
        ConfigFileError: on unreadable JSON, a missing field, or a digest that
            does not match the parameters beside it.
    """
    try:
        body = json.loads(path.read_text())
    except OSError as exc:
        raise ConfigFileError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigFileError(f"{path.name} is not JSON: {exc}") from exc
    if not isinstance(body, dict):
        raise ConfigFileError(f"{path.name} is not a config object")

    missing = [
        name
        for name in ("game_id", "game_uid", "sub_game", "parameters", "config_sha256")
        if name not in body
    ]
    if missing:
        raise ConfigFileError(f"{path.name} is missing {missing}")
    parameters = body["parameters"]
    if not isinstance(parameters, dict):
        raise ConfigFileError(f"{path.name} has parameters that are not an object")

    recomputed = config_sha256(parameters)
    if recomputed != body["config_sha256"]:
        raise ConfigFileError(
            f"{path.name} carries digest {str(body['config_sha256'])[:16]}… but its "
            f"parameters produce {recomputed[:16]}…; the file has been edited since it "
            "was locked, and the two peers no longer agree on the same game"
        )

    agreed = body.get("agreed_between", [])
    if not isinstance(agreed, list) or len(agreed) != 2:
        raise ConfigFileError(f"{path.name} does not name two teams")

    return LockedConfig(
        game_id=str(body["game_id"]),
        game_uid=str(body["game_uid"]),
        sub_game=int(body["sub_game"]),
        parameters=parameters,
        agreed_between=(str(agreed[0]), str(agreed[1])),
    )
