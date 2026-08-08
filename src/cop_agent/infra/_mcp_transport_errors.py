"""HTTP client exception helpers for infra/mcp_transport.py."""

HTTP_CLIENT_MODULES = frozenset({"httpx", "httpcore"})
UPSTREAM_DEAD = frozenset({502, 503, 504})


def from_http_client(error: BaseException) -> bool:
    return type(error).__module__.split(".")[0] in HTTP_CLIENT_MODULES


def why(error: BaseException) -> str:
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        said = str(current).strip()
        if said:
            return f"{said} ({type(current).__name__})"
        current = current.__cause__ or current.__context__
    return f"{type(error).__name__} with no detail"


def upstream_status(error: object) -> int | None:
    code = getattr(getattr(error, "response", None), "status_code", None)
    return code if isinstance(code, int) else None
