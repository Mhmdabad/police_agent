from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_handshake")).items() if not k.startswith("__")})

class TestTheGreetingItself:
    def test_it_normalises_the_url_so_both_sides_record_one_string(self) -> None:
        assert greet("police", f"{PUBLIC_COP}/").public_url == f"{PUBLIC_COP}/mcp"
    def test_it_reports_whether_the_address_routes(self) -> None:
        assert greet("police", PUBLIC_COP).reachable
        assert not greet("police", LOCAL_COP).reachable
    @pytest.mark.parametrize("role", ["cop", "COP", "referee", ""])
    def test_it_refuses_a_role_the_wire_does_not_name(self, role: str) -> None:
        with pytest.raises(HandshakeError, match="role must be one of"):
            greet(role, PUBLIC_COP)
    @pytest.mark.parametrize("group", ["", "   "])
    def test_it_refuses_an_anonymous_team(self, group: str) -> None:
        with pytest.raises(HandshakeError, match="group_id must be set"):
            greet("police", PUBLIC_COP, group=group)
    def test_it_refuses_a_url_it_cannot_parse(self) -> None:
        with pytest.raises(HandshakeError):
            greet("police", "not-a-url")
    def test_it_is_frozen_so_an_agreed_address_cannot_move_afterwards(self) -> None:
        greeting = greet("police", PUBLIC_COP)
        with pytest.raises(AttributeError):
            greeting.public_url = LOCAL_COP  # type: ignore[misc]
