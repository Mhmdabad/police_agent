from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tunnel")).items() if not k.startswith("__")})

class TestWhatCountsAsPublic:
    @pytest.mark.parametrize(
        "host",
        [
            "127.0.0.1",
            "127.1.2.3",
            "::1",
            "localhost",
            "LOCALHOST",
            "agent.localhost",
            "printer.local",
            "svc.internal",
            "10.0.0.7",
            "192.168.1.10",
            "172.16.5.4",
            "169.254.10.1",
            "0.0.0.0",
            "",
            "fe80::1",
            "[::1]",
        ],
    )
    def test_it_refuses_everything_an_opponent_cannot_route_to(self, host: str) -> None:
        assert not host_is_public(host)
    @pytest.mark.parametrize(
        "host",
        ["a1b2.ngrok-free.app", "tunnel.localtonet.com", "8.8.8.8", "2606:4700::1111", "1.1.1.1"],
    )
    def test_it_accepts_addresses_that_route(self, host: str) -> None:
        assert host_is_public(host)
    def test_an_unresolvable_name_is_trusted_rather_than_looked_up(self) -> None:
        assert host_is_public("no-such-host-anywhere.invalid")
