import json
import stat
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast
import pytest
from cop_agent.infra.authorize import Runner, authorize, google_flow, main
from cop_agent.infra.credentials import CREDENTIALS_FILE, CredentialsError
from cop_agent.infra.gmail_auth import SEND_SCOPE
from cop_agent.infra.token_store import TokenError, read
CLIENT = "1234567890-abcdef.apps.googleusercontent.com"
READ_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
DESKTOP: dict[str, Any] = {
    "installed": {
        "client_id": CLIENT,
        "project_id": "uoh26-cops-and-robbers",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_secret": "GOCSPX-not-a-real-secret",
    }
}
GRANTED: dict[str, Any] = {
    "client_id": CLIENT,
    "refresh_token": "1//refresh-not-real",
    "token": "ya29.access-not-real",
    "scopes": [SEND_SCOPE],
    "expiry": "2099-01-01T00:00:00Z",
}
def client_file(tmp_path: Path, body: object = DESKTOP) -> Path:
    path = tmp_path / CREDENTIALS_FILE
    path.write_text(json.dumps(body))
    return path
def returning(body: object, seen: list[Any] | None = None) -> Runner:
    def runner(client: dict[str, Any], scopes: Sequence[str]) -> dict[str, Any]:
        if seen is not None:
            seen.append((client, tuple(scopes)))
        return cast("dict[str, Any]", body)
    return runner
