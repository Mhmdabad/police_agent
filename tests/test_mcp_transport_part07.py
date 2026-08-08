from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mcp_transport")).items() if not k.startswith("__")})

class TestSayingWhyWhenTheExceptionWillNot:
    def test_the_first_thing_with_something_to_say_wins(self) -> None:
        inner = OSError("connection refused")
        outer = ValueError("")
        outer.__cause__ = inner
        assert "connection refused" in why(outer)
    def test_a_cycle_does_not_trap_it(self) -> None:
        first, second = ValueError(""), ValueError("")
        first.__cause__, second.__cause__ = second, first
        assert why(first) == "ValueError with no detail"
    def test_a_plain_message_is_used_directly(self) -> None:
        assert why(OSError("no route to host")).startswith("no route to host")
    def test_the_module_test_is_on_the_top_level_package(self) -> None:
        import httpcore
        import httpx
        assert from_http_client(httpx.ConnectError(""))
        assert from_http_client(httpcore.ConnectError())
        assert not from_http_client(KeyError("ours"))
