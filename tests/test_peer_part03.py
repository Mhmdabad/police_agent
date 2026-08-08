from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_peer")).items() if not k.startswith("__")})

class TestRecordsArriveOutOfOrder:
    def test_stale_reveal_cannot_mask_current_reveal_in_same_payload(self) -> None:
        peer, _, inboxes = a_peer()
        stale = Reveal(step=1, sender="thief", move="S", intent="truth", hint="old", timestamp=WHEN)
        current = Reveal(
            step=2, sender="thief", move="N", intent="truth", hint="now", timestamp=WHEN
        )
        inboxes.audits.put(
            AuditPayload(
                sender="thief",
                records=[stale.to_dict(), current.to_dict()],
                result_claim=UNDECIDED,
                game_uid="series-123",
                sub_game=2,
            )
        )
        assert peer.await_reveal(2) == current
        assert stale.to_dict() not in peer._held
    def test_a_record_we_are_not_waiting_for_is_kept(self) -> None:
        peer, _, inboxes = a_peer()
        early = FinalReveal(sender="thief", nonces={1: "0" * 32}, timestamp=WHEN)
        wanted = Reveal(step=1, sender="thief", move="S", intent="truth", hint="t", timestamp=WHEN)
        inboxes.audits.put(
            AuditPayload(
                sender="thief",
                records=[early.to_dict(), wanted.to_dict()],
                result_claim=UNDECIDED,
                game_uid="series-123",
                sub_game=2,
            )
        )
        assert peer.await_reveal(1).move == "S"
        assert peer.await_final().nonces == {1: "0" * 32}, "the early one was thrown away"
    def test_a_held_record_is_found_without_another_wait(self) -> None:
        peer, _, inboxes = a_peer()
        first = Reveal(step=1, sender="thief", move="S", intent="truth", hint="t", timestamp=WHEN)
        second = Reveal(step=2, sender="thief", move="N", intent="truth", hint="t", timestamp=WHEN)
        inboxes.audits.put(
            AuditPayload(
                sender="thief",
                records=[second.to_dict(), first.to_dict()],
                result_claim=UNDECIDED,
                game_uid="series-123",
                sub_game=2,
            )
        )
        assert peer.await_reveal(1).move == "S"
        assert peer.await_reveal(2).move == "N", "step 2 arrived first and was dropped"
