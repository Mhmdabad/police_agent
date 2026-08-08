from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_localhost_match")).items() if not k.startswith("__")})

class TestTheAcknowledgementLimitIsVisible:
    def test_this_opponent_returns_a_bare_ack(self, played: tuple[Side, Side, Path]) -> None:
        cop, _, _ = played
        peer = played_game(cop).peer
        assert isinstance(peer, McpPeer)
        assert peer.reference_acks == [1, 2, 3]
