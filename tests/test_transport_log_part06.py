from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_transport_log")).items() if not k.startswith("__")})

class TestTheDerivedViews:
    def test_sent_digests_come_out_of_the_log(self) -> None:
        peer = client({"ok": True}, {"ok": True})
        peer.call("receive_turn", {"move": "N"})
        peer.call("receive_turn", {"move": "N"})
        assert [tool for tool, _ in peer.sent] == ["receive_turn", "receive_turn"]
        assert peer.sent[0][1] == peer.sent[1][1]
        assert len(peer.log.of_kind(SENT)) == 2
    def test_relocations_come_out_of_the_log(self) -> None:
        peer = client()
        peer.repoint(MOVED)
        assert peer.relocations == [(URL, MOVED)]
    def test_a_shared_log_collects_from_both(self) -> None:
        log = TransportLog(clock=Ticking())
        settings = ClientSettings(opponent_url=URL, retry_backoff_sec=0.0)
        OpponentClient(Flaky({"ok": True}), settings, log=log).call("negotiate", {})
        OpponentClient(Flaky({"ok": True}), settings, log=log).call("receive_turn", {})
        assert len(log.of_kind(SENT)) == 2
    def test_every_kind_the_client_emits_is_a_declared_kind(self) -> None:
        peer = client(TimeoutError(), *[TimeoutError()] * 4)
        with pytest.raises(OpponentUnreachableError):
            peer.call("receive_turn", {})
        peer.repoint(MOVED)
        assert {event.kind for event in peer.log.events} <= set(KINDS)
