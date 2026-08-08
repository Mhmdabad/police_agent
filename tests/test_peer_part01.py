from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_peer")).items() if not k.startswith("__")})

class TestTheAcknowledgementIsTheResponse:
    def test_a_digest_in_the_answer_is_taken_as_theirs(self) -> None:
        peer, _, _ = a_peer({"ok": True, "acknowledges": OTHER})
        peer.send_commit(a_commitment())
        assert peer.await_ack(1).acknowledges == OTHER
        assert peer.reference_acks == []
    def test_a_bare_ok_falls_back_to_what_we_sent(self) -> None:
        peer, _, _ = a_peer({"ok": True})
        peer.send_commit(a_commitment())
        assert peer.await_ack(1).acknowledges == DIGEST
        assert peer.reference_acks == [1]
    def test_the_acknowledgement_is_attributed_to_them(self) -> None:
        peer, _, _ = a_peer()
        peer.send_commit(a_commitment())
        assert peer.await_ack(1).sender == "thief"
    def test_nothing_extra_crosses_the_wire_for_an_ack(self) -> None:
        peer, transport, _ = a_peer()
        peer.send_commit(a_commitment())
        peer.send_ack(peer.await_ack(1))
        assert [tool for tool, _ in transport.calls] == ["receive_turn"]
    def test_an_ack_for_an_unsent_step_is_a_timeout(self) -> None:
        peer, _, _ = a_peer()
        with pytest.raises(PeerTimeout, match="never answered our commitment"):
            peer.await_ack(7)
