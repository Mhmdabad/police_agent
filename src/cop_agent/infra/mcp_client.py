import dataclasses
import hashlib
import json
import time
from collections.abc import Callable
from typing import Any
from ..shared.config import canonical_bytes
from ._mcp_client_settings import (
    OPPONENT_URL_ENV as OPPONENT_URL_ENV,
)
from ._mcp_client_settings import (
    RETRY_KEY as RETRY_KEY,
)
from ._mcp_client_settings import (
    ClientSettings as ClientSettings,
)
from ._mcp_client_settings import (
    OpponentUnreachableError as OpponentUnreachableError,
)
from ._mcp_client_settings import (
    PeerNotReadyError as PeerNotReadyError,
)
from ._mcp_client_settings import (
    Transport as Transport,
)
from ._mcp_client_settings import (
    deferred as deferred,
)
from .transport_log import (
    CONNECT,
    RECONNECT,
    RETRY,
    SENT,
    TIMEOUT,
    UNREACHABLE,
    TransportLog,
)
class OpponentClient:
    def __init__(
        self,
        transport: Transport,
        settings: ClientSettings,
        sleep: Callable[[float], None] | None = None,
        log: TransportLog | None = None,
        on_attempt: Callable[[str], None] = lambda _: None,
    ) -> None:
        self._transport = transport
        self._settings = settings
        self._sleep = time.sleep if sleep is None else sleep
        self.attempts = 0
        self.log = log if log is not None else TransportLog()
        self.on_attempt = on_attempt
        self._connected: set[str] = set()
    @property
    def opponent_url(self) -> str:
        return self._settings.opponent_url
    @property
    def sent(self) -> list[tuple[str, str]]:
        return [(event.tool, event.detail) for event in self.log.of_kind(SENT)]
    @property
    def relocations(self) -> list[tuple[str, str]]:
        return [(event.detail, event.url) for event in self.log.of_kind(RECONNECT)]
    def repoint(self, url: str) -> str:
        was = self._settings.opponent_url
        self._settings = dataclasses.replace(self._settings, opponent_url=url)
        if self._settings.opponent_url != was:
            self.log.record(RECONNECT, "", self._settings.opponent_url, detail=was)
        return was
    def call(self, tool: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = self._settings.opponent_url
        frozen = canonical_bytes(payload)
        self.log.record(SENT, tool, url, detail=hashlib.sha256(frozen).hexdigest())
        last: Exception | None = None
        shut = ""
        for attempt in range(self._settings.max_retries + 1):
            self.attempts += 1
            self.on_attempt(tool)
            try:
                answer = self._transport.call(
                    url, tool, json.loads(frozen), self._settings.response_timeout_sec
                )
            except (TimeoutError, ConnectionError, OSError) as exc:
                last = exc
                self.log.record(TIMEOUT, tool, url, detail=f"{type(exc).__name__}: {exc}")
                self._back_off(attempt, tool, url)
            else:
                if url not in self._connected:
                    self._connected.add(url)
                    self.log.record(CONNECT, tool, url)
                if not deferred(answer):
                    return answer
                shut = str(answer.get("detail", ""))
                self.log.record(TIMEOUT, tool, url, detail=f"deferred: {shut}")
                self._back_off(attempt, tool, url)
        spent = f"{tool} failed after {self._settings.max_retries + 1} attempts against {url}"
        self.log.record(UNREACHABLE, tool, url, detail=shut or str(last))
        if shut:
            raise PeerNotReadyError(f"{spent}; the last answer was {shut!r}")
        raise OpponentUnreachableError(spent) from last
    def _back_off(self, attempt: int, tool: str, url: str) -> None:
        if attempt >= self._settings.max_retries:
            return
        self.log.record(
            RETRY,
            tool,
            url,
            detail=(
                f"attempt {attempt + 2} of {self._settings.max_retries + 1} "
                f"after {self._settings.retry_backoff_sec:g}s"
            ),
        )
        self._sleep(self._settings.retry_backoff_sec)
