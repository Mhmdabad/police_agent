import asyncio
import contextlib
import json
import threading
from dataclasses import dataclass, field
from typing import Any
from fastmcp import Client
from ._mcp_transport_errors import (
    HTTP_CLIENT_MODULES as HTTP_CLIENT_MODULES,
)
from ._mcp_transport_errors import (
    UPSTREAM_DEAD as UPSTREAM_DEAD,
)
from ._mcp_transport_errors import (
    from_http_client as from_http_client,
)
from ._mcp_transport_errors import (
    upstream_status as upstream_status,
)
from ._mcp_transport_errors import (
    why as why,
)
SHUTDOWN_GRACE = 5.0
@dataclass
class FastMcpTransport:
    _loop: asyncio.AbstractEventLoop | None = field(default=None, init=False, repr=False)
    _thread: threading.Thread | None = field(default=None, init=False, repr=False)
    _client: Any = field(default=None, init=False, repr=False)
    _connected_to: str = field(default="", init=False, repr=False)
    def call(self, url: str, tool: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        try:
            answer = asyncio.run_coroutine_threadsafe(
                self._call(url, tool, payload, timeout), self._running_loop()
            ).result(timeout + SHUTDOWN_GRACE)
        except TypeError:
            raise  # their tool answered badly; the connection is fine
        except BaseException:
            self.drop()
            raise
        return answer
    def drop(self) -> None:
        client, self._client, self._connected_to = self._client, None, ""
        loop = self._loop
        if client is None or loop is None or loop.is_closed():
            return
        with contextlib.suppress(Exception):  # see the docstring
            asyncio.run_coroutine_threadsafe(client.__aexit__(None, None, None), loop).result(
                SHUTDOWN_GRACE
            )
    def close(self) -> None:
        self.drop()
        loop, self._loop, thread, self._thread = self._loop, None, self._thread, None
        if loop is not None and not loop.is_closed():
            loop.call_soon_threadsafe(loop.stop)
        if thread is not None:
            thread.join(timeout=SHUTDOWN_GRACE)
    def _running_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(
                target=self._loop.run_forever, name="mcp-client", daemon=True
            )
            self._thread.start()
        return self._loop
    async def _session(self, url: str) -> Any:  # noqa: ANN401 - whatever FastMCP returns
        if self._client is not None and self._connected_to == url:
            return self._client
        if self._client is not None:
            await self._client.__aexit__(None, None, None)
        client = Client(url)
        self._client = await client.__aenter__()  # type: ignore[no-untyped-call]
        self._connected_to = url
        return self._client
    async def _call(
        self, url: str, tool: str, payload: dict[str, Any], timeout: float
    ) -> dict[str, Any]:
        try:
            client = await self._session(url)
            answer = await client.call_tool(tool, payload, timeout=timeout)
        except (TimeoutError, ConnectionError, OSError):
            raise  # already the vocabulary the retry budget understands
        except Exception as exc:
            status = upstream_status(exc)
            if status in UPSTREAM_DEAD:
                raise ConnectionError(
                    f"could not reach {url}: the tunnel answered {status}, which means "
                    "it is up but nothing is listening behind it — their agent is not "
                    "running, or their tunnel points at a different port"
                ) from exc
            if isinstance(exc, RuntimeError):
                raise ConnectionError(f"could not reach {url}: {exc}") from exc
            if from_http_client(exc):
                raise ConnectionError(
                    f"could not reach {url}: {why(exc)}. The request never completed, "
                    "so either the tunnel is no longer forwarding — free tunnels expire "
                    "and their addresses change on restart — or the opponent's agent has "
                    "stopped"
                ) from exc
            raise
        data = answer.data
        if isinstance(data, str):
            with contextlib.suppress(ValueError):
                data = json.loads(data)
        if not isinstance(data, dict):
            raise TypeError(
                f"{tool} at {url} returned {type(data).__name__}, not an object; every "
                "tool in this protocol answers with a mapping, and a peer that does not "
                "is not speaking it"
            )
        return data
