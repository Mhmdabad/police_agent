from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_handshake")).items() if not k.startswith("__")})

class TestWhatCountsAsARotatedTunnel:
    def test_the_same_peer_at_a_new_address_is_accepted(self) -> None:
        check_rotation(greet("thief", PUBLIC_THIEF), greet("thief", ROTATED_THIEF))
    @pytest.mark.parametrize(
        ("field", "fresh"),
        [
            ("role", ("police", ROTATED_THIEF, "s82kma9e", PROTOCOL_VERSION)),
            ("group_id", ("thief", ROTATED_THIEF, "another-team", PROTOCOL_VERSION)),
            ("protocol_version", ("thief", ROTATED_THIEF, "s82kma9e", "2.0")),
        ],
    )
    def test_anything_but_the_address_moving_is_a_different_peer(
        self, field: str, fresh: tuple[str, str, str, str]
    ) -> None:
        role, url, group, version = fresh
        with pytest.raises(HandshakeError, match=field):
            check_rotation(greet("thief", PUBLIC_THIEF), greet(role, url, group, version))
