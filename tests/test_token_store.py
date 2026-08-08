import json
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
import pytest
from cop_agent.infra.gmail_auth import SEND_SCOPE
from cop_agent.infra.token_store import (
    TOKEN_PATH_ENV,
    Exchange,
    StoredToken,
    TokenError,
    google_refresh,
    read,
    refresh,
    save,
    token_path,
)
CLIENT = "1234567890-abcdef.apps.googleusercontent.com"
OTHER = "9999999999-zzzzzz.apps.googleusercontent.com"
READ_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
GOOD: dict[str, Any] = {
    "client_id": CLIENT,
    "refresh_token": "1//refresh-not-real",
    "token": "ya29.access-not-real",
    "scopes": [SEND_SCOPE],
    "expiry": "2099-01-01T00:00:00Z",
}
def stored(tmp_path: Path, **overrides: object) -> Path:
    path = tmp_path / "token_cop.json"
    path.write_text(json.dumps({**GOOD, **overrides}))
    return path
