from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_peer")).items() if not k.startswith("__")})

class TestWhatCrossesTheWire:
    def test_a_commit_goes_as_a_turn_message(self) -> None:
        peer, transport, _ = a_peer()
        peer.send_commit(a_commitment())
        tool, payload = transport.calls[0]
        assert tool == "receive_turn"
        assert payload["message"]["commit"] == DIGEST
    def test_a_reveal_goes_as_an_audit_record(self) -> None:
        peer, transport, _ = a_peer()
        peer.send_reveal(
            Reveal(step=1, sender="police", move="N", intent="truth", hint="h", timestamp=WHEN)
        )
        tool, payload = transport.calls[0]
        assert tool == "submit_audit"
        assert payload["payload"]["records"][0]["move"] == "N"
    def test_a_mid_game_reveal_claims_nothing_yet(self) -> None:
        peer, transport, _ = a_peer()
        peer.send_reveal(
            Reveal(step=1, sender="police", move="N", intent="truth", hint="h", timestamp=WHEN)
        )
        assert transport.calls[0][1]["payload"]["result_claim"] == UNDECIDED
    def test_the_final_reveal_carries_our_claim(self) -> None:
        peer, transport, _ = a_peer()
        peer.result_claim = "captured"
        peer.send_final(FinalReveal(sender="police", nonces={1: "0" * 32}, timestamp=WHEN))
        assert transport.calls[0][1]["payload"]["result_claim"] == "captured"
    def test_a_final_reveal_with_no_claim_still_says_something(self) -> None:
        peer, transport, _ = a_peer()
        peer.send_final(FinalReveal(sender="police", nonces={1: "0" * 32}, timestamp=WHEN))
        assert transport.calls[0][1]["payload"]["result_claim"] == UNDECIDED
