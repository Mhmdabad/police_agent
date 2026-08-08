from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_declaration")).items() if not k.startswith("__")})

class TestTheEndTimeIsAddedAfterwards:
    def test_it_starts_empty(self) -> None:
        assert declared().ended_at == ""
    def test_concluding_records_it(self) -> None:
        finished = declared().concluded("2026-08-05T13:04:00Z", KEY)
        assert finished.ended_at == "2026-08-05T13:04:00Z"
    def test_concluding_re_signs(self) -> None:
        finished = declared().concluded("2026-08-05T13:04:00Z", KEY)
        assert finished.signature != declared().signature
        assert finished.signature != UNSIGNED
    def test_concluding_returns_a_copy(self) -> None:
        original = declared()
        original.concluded("2026-08-05T13:04:00Z", KEY)
        assert original.ended_at == ""
    def test_the_pre_game_fields_are_unchanged(self) -> None:
        finished = declared().concluded("2026-08-05T13:04:00Z", KEY)
        before, after = declared().content(), finished.content()
        del before["ended_at"], after["ended_at"]
        assert before == after
    def test_it_refuses_an_empty_end_time(self) -> None:
        with pytest.raises(DeclarationError, match="needs an end time"):
            declared().concluded("", KEY)
