import json
import urllib.request
from typing import Any
import pytest
from cop_agent.infra.tunnel import (
    MCP_PATH,
    NGROK_API,
    PUBLIC_URL_ENV,
    NotPublicError,
    PublicEndpoint,
    discover,
    from_ngrok,
    host_is_public,
    normalise,
    read_ngrok_api,
    rehearsal_url,
)
PUBLIC = "https://a1b2c3d4.ngrok-free.app"
def ngrok_body(*urls: str) -> str:
    return json.dumps({"tunnels": [{"public_url": u, "proto": u.split(":")[0]} for u in urls]})
