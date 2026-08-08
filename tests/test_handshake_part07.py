from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_handshake")).items() if not k.startswith("__")})

class TestPeering:
    def test_it_carries_fresh_addresses_into_the_next_sub_game(self) -> None:
        later = opened().rotate(greet("police", PUBLIC_COP), greet("thief", ROTATED_THIEF), 2)
        assert later.sub_game == 2
        assert later.theirs.public_url == f"{ROTATED_THIEF}/mcp"
    def test_a_mid_sub_game_change_is_refused(self) -> None:
        with pytest.raises(HandshakeError, match="only change between sub-games"):
            opened(2).rotate(greet("police", PUBLIC_COP), greet("thief", ROTATED_THIEF), 2)
    def test_going_backwards_is_refused(self) -> None:
        with pytest.raises(HandshakeError, match="does not follow"):
            opened(3).rotate(greet("police", PUBLIC_COP), greet("thief", ROTATED_THIEF), 2)
    def test_a_rotation_still_has_to_be_playable(self) -> None:
        with pytest.raises(HandshakeError, match="routes nowhere"):
            opened().rotate(greet("police", PUBLIC_COP), greet("thief", LOCAL_THIEF), 2)
    def test_it_reports_only_the_addresses_that_actually_moved(self) -> None:
        first = opened()
        assert first.relocations(first.rotate(*(first.ours, first.theirs), 2)) == {}
    def test_it_names_both_sides_when_both_rotate(self) -> None:
        first = opened()
        later = first.rotate(greet("police", ROTATED_COP), greet("thief", ROTATED_THIEF), 2)
        assert first.relocations(later) == {
            "police": (f"{PUBLIC_COP}/mcp", f"{ROTATED_COP}/mcp"),
            "thief": (f"{PUBLIC_THIEF}/mcp", f"{ROTATED_THIEF}/mcp"),
        }
    def test_it_is_frozen_so_the_agreed_pair_cannot_drift(self) -> None:
        with pytest.raises(AttributeError):
            opened().sub_game = 9  # type: ignore[misc]
