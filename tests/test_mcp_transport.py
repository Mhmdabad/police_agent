import socket
import threading
import time
from collections.abc import Iterator
import pytest
from cop_agent.infra.inboxes import PeerInboxes
from cop_agent.infra.mcp_client import (
    ClientSettings,
    OpponentClient,
    OpponentUnreachableError,
    Transport,
)
from cop_agent.infra.mcp_server import ServerSettings, build, serve
from cop_agent.infra.mcp_transport import (
    UPSTREAM_DEAD,
    FastMcpTransport,
    from_http_client,
    upstream_status,
    why,
)
def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = int(probe.getsockname()[1])
    return port
@pytest.fixture(scope="module")
def opponent() -> Iterator[tuple[str, PeerInboxes]]:
    inboxes = PeerInboxes()
    port = free_port()
    host = build(inboxes, name="stand-in-opponent")
    thread = threading.Thread(
        target=serve,
        args=(host, ServerSettings(port=port, host="127.0.0.1")),
        daemon=True,
    )
    thread.start()
    url = f"http://127.0.0.1:{port}/mcp"
    deadline = time.monotonic() + 20.0
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.05)
    else:  # pragma: no cover - only on a machine that cannot bind at all
        pytest.fail("the stand-in opponent never came up")
    yield url, inboxes
