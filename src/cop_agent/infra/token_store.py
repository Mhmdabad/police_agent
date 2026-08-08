"""``token.json``: reading it, judging it, and writing it back after a refresh."""

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .gmail_auth import SCOPES, ScopeError, check_granted

TOKEN_FILE = "token.json"
"""Default name. Overridden per agent — see :func:`token_path`."""

TOKEN_PATH_ENV = "GMAIL_TOKEN_PATH"
"""Explicit override, so the two agents never share a token by accident."""

REAUTHORIZE = (
    "run `python -m {package}.infra.authorize` to authorize again; note that an app "
    "in Testing issues a refresh token that expires after seven days"
)


from ._token_reader import (
    REAUTHORIZE as REAUTHORIZE,
)
from ._token_reader import (
    ROLE_FIELD as ROLE_FIELD,
)
from ._token_reader import (
    StoredToken as StoredToken,
)
from ._token_reader import (
    TokenError as TokenError,
)
from ._token_reader import (
    read as read,
)
from ._token_reader import (
    token_path as token_path,
)

Exchange = Callable[[str, dict[str, Any]], dict[str, Any]]
"""Takes the refresh token and the client section; returns the refreshed body."""


def google_refresh(refresh_token: str, client: dict[str, Any]) -> dict[str, Any]:
    """Exchange a refresh token for a fresh access token. The only network call.

    Imported inside the function so the rest of the mail path does not depend
    on the Google library being installed or importable.
    """
    from google.auth.transport.requests import Request  # noqa: PLC0415
    from google.oauth2.credentials import Credentials  # noqa: PLC0415

    # The Google library's own functions are untyped, so strict mode objects to
    # calling them. Ignored here, on three lines, rather than relaxing the rule
    # for a module that also holds the decisions worth type-checking.
    credentials = Credentials(  # type: ignore[no-untyped-call]
        token=None,
        refresh_token=refresh_token,
        token_uri=client["token_uri"],
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        scopes=list(SCOPES),
    )
    credentials.refresh(Request())  # type: ignore[no-untyped-call]
    parsed = json.loads(credentials.to_json())  # type: ignore[no-untyped-call]
    return dict(parsed)


def refresh(
    path: Path,
    stored: StoredToken,
    client: dict[str, Any],
    exchange: Exchange | None = None,
) -> StoredToken:
    """Mint a fresh access token from the refresh token, and write it back.

    This is what makes the agent able to report unattended: the access token
    lasts an hour, the refresh token replaces it silently, and the file on disk
    is updated so the next process starts from the new one.

    The result is judged before it is written — same scope rules, same refresh
    token requirement. A refresh that came back over-scoped, or without a
    refresh token to use next time, is not an improvement on what we had, and
    writing it would replace a good credential with a worse one.

    Raises:
        TokenError: if the exchange returns something unusable. Nothing is
            written in that case, so the existing token survives a bad refresh.
    """
    body = (exchange or google_refresh)(stored.refresh_token, client)
    if not isinstance(body, dict):
        raise TokenError(f"the refresh returned {type(body).__name__}, not a credential")

    body.setdefault(ROLE_FIELD, stored.role)
    body.setdefault("refresh_token", stored.refresh_token)
    body.setdefault("client_id", stored.client_id)

    try:
        check_granted(body.get("scopes", body.get("scope")))
    except ScopeError as exc:
        raise TokenError(f"the refreshed credential is not one we may hold: {exc}") from exc
    if not body.get("refresh_token"):
        raise TokenError(
            "the refresh returned no refresh token, so the next one would have nothing "
            "to use; keeping the existing credential rather than replacing it with a "
            "worse one"
        )

    save(path, body)
    return read(path, stored.client_id, role=stored.role)


def save(path: Path, body: dict[str, Any]) -> Path:
    """Write a credential back after a refresh, readable only by this user.

    The permissions are set **before** anything is written. Creating the file
    world-readable and narrowing it afterwards leaves a window in which the
    refresh token is readable by every account on the machine, and on a shared
    university machine that window is the whole exposure.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(handle, "w") as stream:
        json.dump(body, stream, indent=2, sort_keys=True)
        stream.write("\n")
    os.chmod(path, 0o600)
    return path
