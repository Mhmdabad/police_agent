"""The public address this peer is reachable at.

Parses, validates, and discovers public MCP tunnel URLs (e.g. via ngrok or env).
"""

import ipaddress
import json
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse, urlunparse

MCP_PATH = "/mcp"
PUBLIC_URL_ENV = "PUBLIC_URL"
NGROK_API = "http://127.0.0.1:4040/api/tunnels"
SCHEMES = ("https", "http")
LOCAL_NAMES = frozenset({"localhost", ""})
LOCAL_SUFFIXES = (".localhost", ".local", ".internal", ".home.arpa")


class NotPublicError(ValueError):
    """Raised when a URL could not be reached by an opponent elsewhere."""


def host_is_public(host: str) -> bool:
    """Whether ``host`` could be routed to from another machine on the internet."""
    name = host.strip().lower().strip("[]")
    if name in LOCAL_NAMES or name.endswith(LOCAL_SUFFIXES):
        return False
    try:
        address = ipaddress.ip_address(name)
    except ValueError:
        return True
    return not (
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


def normalise(raw: str, path: str = MCP_PATH) -> str:
    """Canonicalise a tunnel URL into the form the opponent will call.

    A tunnel prints its base address (``https://a1b2.ngrok-free.app``), while
    the opponent needs the MCP endpoint on it. Appending the path here rather
    than expecting whoever copies the URL to remember removes the most likely
    transcription error in the whole handshake.

    Raises:
        NotPublicError: if the scheme is unusable or the host is missing.
    """
    parsed = urlparse(raw.strip())
    if parsed.scheme not in SCHEMES:
        raise NotPublicError(f"{raw!r} must use one of {list(SCHEMES)}, got {parsed.scheme!r}")
    if not parsed.hostname:
        raise NotPublicError(f"{raw!r} has no host")
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/") or path, "", "", ""))


@dataclass(frozen=True, slots=True)
class PublicEndpoint:
    """A verified public address for one peer's MCP server."""

    url: str

    def __post_init__(self) -> None:
        canonical = normalise(self.url)
        object.__setattr__(self, "url", canonical)
        host = urlparse(canonical).hostname or ""
        if not host_is_public(host):
            raise NotPublicError(
                f"{canonical} is not reachable from another machine (host {host!r}); "
                "start a tunnel and advertise the address it prints. Running on "
                "localhost is permitted only during early coding."
            )

    @property
    def host(self) -> str:
        return urlparse(self.url).hostname or ""

    @property
    def secure(self) -> bool:
        """Whether the tunnel terminates TLS. Recorded, not required."""
        return urlparse(self.url).scheme == "https"


def from_ngrok(payload: str | bytes) -> str:
    """Pull the public URL out of a response from :data:`NGROK_API`."""
    try:
        body: Any = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise NotPublicError(f"ngrok API returned no usable JSON: {exc}") from exc
    tunnels = body.get("tunnels") if isinstance(body, dict) else None
    found = {
        urlparse(str(t["public_url"])).scheme: str(t["public_url"])
        for t in tunnels or []
        if isinstance(t, dict) and t.get("public_url")
    }
    for scheme in SCHEMES:
        if scheme in found:
            return found[scheme]
    raise NotPublicError(f"ngrok API listed no {list(SCHEMES)} tunnel: {body!r}")


def read_ngrok_api(url: str = NGROK_API, timeout: float = 2.0) -> bytes:
    """Fetch :data:`NGROK_API`. Short timeout: it is a loopback call or nothing.

    Two seconds because the only two outcomes are an immediate answer from a
    local process and a connection refused. Waiting longer would delay startup
    for every team that uses Localtonet instead.
    """
    with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 - fixed loopback
        return bytes(response.read())


def rehearsal_url(environ: Mapping[str, str], port: int = 8801, path: str = MCP_PATH) -> str:
    """The address to advertise during a **solo rehearsal**, loopback allowed."""
    return normalise(environ.get(PUBLIC_URL_ENV, "").strip() or f"http://127.0.0.1:{port}", path)


def discover(
    environ: Mapping[str, str],
    ngrok_reader: Callable[[], str | bytes] | None = read_ngrok_api,
) -> PublicEndpoint | None:
    """The address to advertise, or ``None`` when this peer is not exposed yet."""
    explicit = environ.get(PUBLIC_URL_ENV, "").strip()
    if explicit:
        return PublicEndpoint(explicit)
    if ngrok_reader is None:
        return None
    try:
        payload = ngrok_reader()
    except OSError:
        return None
    return PublicEndpoint(from_ngrok(payload))
