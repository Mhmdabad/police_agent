from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_handshake")).items() if not k.startswith("__")})

class TestWhoMayPlayWhom:
    def test_two_public_peers_agree(self) -> None:
        check(greet("police", PUBLIC_COP), greet("thief", PUBLIC_THIEF))
    def test_a_protocol_mismatch_is_refused_before_the_first_move(self) -> None:
        with pytest.raises(HandshakeError, match="wire contract must match"):
            check(greet("police", PUBLIC_COP), greet("thief", PUBLIC_THIEF, version="0.9"))
    def test_two_peers_claiming_one_role_is_refused(self) -> None:
        with pytest.raises(HandshakeError, match="no capture target"):
            check(greet("thief", PUBLIC_THIEF), greet("thief", PUBLIC_COP))
    def test_a_public_peer_refuses_a_loopback_opponent(self) -> None:
        with pytest.raises(HandshakeError, match="routes nowhere from here"):
            check(greet("police", PUBLIC_COP), greet("thief", LOCAL_THIEF))
    def test_two_loopback_peers_agree_because_that_is_the_local_test_loop(self) -> None:
        check(greet("police", LOCAL_COP), greet("thief", LOCAL_THIEF))
    def test_a_loopback_peer_accepts_a_public_opponent(self) -> None:
        check(greet("police", LOCAL_COP), greet("thief", PUBLIC_THIEF))
