from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_match")).items() if not k.startswith("__")})

class TestWhoeverStartsFirstMustNotBePunished:
    @staticmethod
    def greeting() -> Greeting:
        return Greeting(
            role="police",
            group_id="s82kma9e",
            public_url="https://ours.ngrok.io/mcp",
            protocol_version=PROTOCOL_VERSION,
        )
    class Peer:
        def __init__(self, up_after: int) -> None:
            self.up_after = up_after
            self.attempts = 0
            self.opened = False
        def try_announce(self, ours: Greeting) -> bool:
            self.attempts += 1
            return self.attempts > self.up_after
        def open_series(self, ours: Greeting, directory: Path, game_id: str) -> Peering:
            self.opened = True
            return Peering(ours=ours, theirs=ours, sub_game=1)
    def test_it_keeps_announcing_until_they_appear(self, tmp_path: Path) -> None:
        peer = self.Peer(up_after=3)
        await_opponent(peer, self.greeting(), tmp_path, "g", sleep=lambda _: None)  # type: ignore[arg-type]
        assert peer.attempts == 4
        assert peer.opened
    def test_an_opponent_already_up_costs_no_wait(self, tmp_path: Path) -> None:
        slept: list[float] = []
        peer = self.Peer(up_after=0)
        await_opponent(peer, self.greeting(), tmp_path, "g", sleep=slept.append)  # type: ignore[arg-type]
        assert slept == []
    def test_it_gives_up_eventually(self, tmp_path: Path) -> None:
        clock = iter([0.0, 0.0, 999.0, 999.0])
        with pytest.raises(StartupTimeout, match="never came up"):
            await_opponent(
                self.Peer(up_after=99),  # type: ignore[arg-type]
                self.greeting(),
                tmp_path,
                "g",
                patience=10.0,
                now=lambda: next(clock),
                sleep=lambda _: None,
            )
    def test_the_message_says_what_to_check(self, tmp_path: Path) -> None:
        clock = iter([0.0, 0.0, 999.0, 999.0])
        with pytest.raises(StartupTimeout, match="their tunnel points at"):
            await_opponent(
                self.Peer(up_after=99),  # type: ignore[arg-type]
                self.greeting(),
                tmp_path,
                "g",
                patience=10.0,
                now=lambda: next(clock),
                sleep=lambda _: None,
            )
    def test_only_the_announcement_is_retried(self, tmp_path: Path) -> None:
        peer = self.Peer(up_after=1)
        await_opponent(peer, self.greeting(), tmp_path, "g", sleep=lambda _: None)  # type: ignore[arg-type]
        assert peer.opened, "the handshake proper should run exactly once, unretried"
