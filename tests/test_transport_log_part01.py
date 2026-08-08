from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_transport_log")).items() if not k.startswith("__")})

class TestTimestamps:
    def test_they_are_utc_because_two_peers_compare_logs(self) -> None:
        assert now_utc().endswith("+00:00")
    def test_they_carry_milliseconds(self) -> None:
        assert re.search(r"\.\d{3}\+00:00$", now_utc())
