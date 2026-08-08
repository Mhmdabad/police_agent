from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_transport_log")).items() if not k.startswith("__")})

class TestWhatTheClientRecords:
    def test_a_first_success_records_a_connection(self) -> None:
        peer = client({"ok": True})
        peer.call("negotiate", {})
        assert [event.kind for event in peer.log.events] == [SENT, CONNECT]
    def test_it_connects_once_per_address_not_once_per_call(self) -> None:
        peer = client({"ok": True}, {"ok": True})
        peer.call("negotiate", {})
        peer.call("receive_turn", {})
        assert len(peer.log.of_kind(CONNECT)) == 1
    def test_a_failed_attempt_names_the_error(self) -> None:
        peer = client(ConnectionError("tunnel refused"), {"ok": True})
        peer.call("receive_turn", {})
        assert "ConnectionError: tunnel refused" in peer.log.of_kind(TIMEOUT)[0].detail
    def test_a_retry_says_which_attempt_of_how_many(self) -> None:
        peer = client(TimeoutError(), TimeoutError(), {"ok": True})
        peer.call("receive_turn", {})
        assert [event.detail for event in peer.log.of_kind(RETRY)] == [
            "attempt 2 of 4 after 0s",
            "attempt 3 of 4 after 0s",
        ]
    def test_the_last_attempt_is_not_followed_by_a_retry(self) -> None:
        peer = client(*[TimeoutError()] * 4)
        with pytest.raises(OpponentUnreachableError):
            peer.call("receive_turn", {})
        assert len(peer.log.of_kind(TIMEOUT)) == 4
        assert len(peer.log.of_kind(RETRY)) == 3
    def test_exhaustion_is_the_line_that_becomes_a_technical_loss(self) -> None:
        peer = client(*[TimeoutError("silent")] * 4)
        with pytest.raises(OpponentUnreachableError):
            peer.call("receive_turn", {})
        assert peer.log.of_kind(UNREACHABLE)[0].url == URL
    def test_a_relocation_records_where_traffic_used_to_go(self) -> None:
        peer = client()
        peer.repoint(MOVED)
        moved = peer.log.of_kind(RECONNECT)[0]
        assert (moved.detail, moved.url) == (URL, MOVED)
    def test_repointing_to_the_same_address_records_nothing(self) -> None:
        peer = client()
        peer.repoint(URL)
        assert peer.log.events == []
    def test_the_whole_sequence_reads_in_order(self) -> None:
        peer = client(TimeoutError("gone"), {"ok": True})
        peer.call("receive_turn", {"move": "N"})
        assert [event.kind for event in peer.log.events] == [SENT, TIMEOUT, RETRY, CONNECT]
