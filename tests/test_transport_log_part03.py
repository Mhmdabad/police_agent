from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_transport_log")).items() if not k.startswith("__")})

class TestTheLog:
    def test_it_keeps_events_in_order(self) -> None:
        log = TransportLog(clock=Ticking())
        log.record(CONNECT, "negotiate", URL)
        log.record(SENT, "receive_turn", URL, "abc")
        assert [event.kind for event in log.events] == [CONNECT, SENT]
    def test_it_filters_by_kind(self) -> None:
        log = TransportLog(clock=Ticking())
        log.record(TIMEOUT, "receive_turn", URL)
        log.record(SENT, "receive_turn", URL)
        log.record(TIMEOUT, "negotiate", URL)
        assert len(log.of_kind(TIMEOUT)) == 2
    def test_it_lists_addresses_in_the_order_they_were_adopted(self) -> None:
        log = TransportLog(clock=Ticking())
        log.record(CONNECT, "negotiate", URL)
        log.record(SENT, "receive_turn", URL)
        log.record(RECONNECT, "", MOVED, detail=URL)
        assert log.addresses == [URL, MOVED]
    def test_an_empty_log_says_so_rather_than_rendering_nothing(self) -> None:
        assert "no transport events" in TransportLog().render()
        assert "no transport events" in TransportLog().summary()
    def test_the_summary_counts_each_kind(self) -> None:
        log = TransportLog(clock=Ticking())
        for _ in range(3):
            log.record(TIMEOUT, "receive_turn", URL)
        log.record(SENT, "receive_turn", URL)
        assert "timeout 3" in log.summary()
        assert "sent 1" in log.summary()
    def test_the_render_ends_with_the_summary(self) -> None:
        log = TransportLog(clock=Ticking())
        log.record(SENT, "receive_turn", URL, "abc")
        assert log.render().rstrip().endswith(log.summary())
    def test_to_dicts_is_the_machine_form(self) -> None:
        log = TransportLog(clock=Ticking())
        log.record(SENT, "receive_turn", URL, "abc")
        assert log.to_dicts() == [
            {
                "at": "2026-08-04T09:00:00.001+00:00",
                "kind": SENT,
                "tool": "receive_turn",
                "url": URL,
                "detail": "abc",
            }
        ]
