"""Token reading and StoredToken definition for infra/token_store.py."""

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .gmail_auth import ScopeError, check_granted

TOKEN_PATH_ENV = "GMAIL_TOKEN_PATH"
ROLE_FIELD = "declared_role"
REAUTHORIZE = (
    "run `python -m {package}.infra.authorize` to authorize again; note that an app "
    "in Testing issues a refresh token that expires after seven days"
)


class TokenError(ValueError):
    """Raised when a stored credential exists but must not be used."""


def token_path(package: str, environ: "dict[str, str] | None" = None) -> Path:
    chosen = (environ if environ is not None else dict(os.environ)).get(TOKEN_PATH_ENV)
    return Path(chosen) if chosen else Path(f"token_{package.split('_')[0]}.json")


@dataclass(frozen=True, slots=True)
class StoredToken:
    """A credential read from disk, already checked."""

    client_id: str
    refresh_token: str
    scopes: tuple[str, ...]
    expiry: datetime | None = None
    role: str = ""

    @property
    def expired(self) -> bool:
        return self.expiry is not None and self.expiry <= datetime.now(UTC)

    @property
    def summary(self) -> str:
        state = "expired" if self.expired else "current"
        return (
            f"token for client {self.client_id.split('.')[0]}… ({state}, {len(self.scopes)} scope)"
        )


def read(path: Path, client_id: str, package: str = "cop_agent", role: str = "") -> StoredToken:
    hint = REAUTHORIZE.format(package=package)
    try:
        body = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise TokenError(f"no {path.name}; {hint}") from exc
    except OSError as exc:
        raise TokenError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise TokenError(f"{path.name} is not JSON: {exc}; delete it and {hint}") from exc

    if not isinstance(body, dict):
        raise TokenError(f"{path.name} is not a token object; delete it and {hint}")

    try:
        scopes = check_granted(body.get("scopes", body.get("scope")))
    except ScopeError as exc:
        raise TokenError(f"{path.name}: {exc}. Then {hint}") from exc

    refresh = body.get("refresh_token")
    if not isinstance(refresh, str) or not refresh:
        raise TokenError(f"{path.name} has no refresh token. {hint}")

    stored = str(body.get("client_id", ""))
    if stored != client_id:
        raise TokenError(f"{path.name} was minted for a different client. {hint}")

    declared = str(body.get(ROLE_FIELD, ""))
    if role and declared and declared != role:
        raise TokenError(f"{path.name} was authorized by the {declared} agent. {hint}")

    return StoredToken(
        client_id=stored,
        refresh_token=refresh,
        scopes=scopes,
        expiry=_expiry(body.get("expiry")),
        role=declared,
    )


def _expiry(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
