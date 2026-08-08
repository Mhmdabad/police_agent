from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_transport_log")).items() if not k.startswith("__")})

class TestEvent:
    def test_it_renders_one_line(self) -> None:
        line = str(
            Event("2026-08-04T09:00:00.000+00:00", TIMEOUT, "receive_turn", URL, "no answer")
        )
        assert "\n" not in line
        assert all(part in line for part in (TIMEOUT, "receive_turn", URL, "no answer"))
    def test_a_toolless_event_still_lines_up(self) -> None:
        assert "-" in str(Event("2026-08-04T09:00:00.000+00:00", RECONNECT, "", URL))
    def test_an_unknown_kind_is_refused(self) -> None:
        with pytest.raises(ValueError, match="kind must be one of"):
            Event("2026-08-04T09:00:00.000+00:00", "vibes", "receive_turn", URL)
    def test_it_is_frozen(self) -> None:
        event = Event("2026-08-04T09:00:00.000+00:00", SENT, "receive_turn", URL)
        with pytest.raises(AttributeError):
            event.kind = TIMEOUT  # type: ignore[misc]
    def test_it_serialises_every_field(self) -> None:
        event = Event("2026-08-04T09:00:00.000+00:00", SENT, "receive_turn", URL, "abc")
        assert set(event.to_dict()) == {"at", "kind", "tool", "url", "detail"}
