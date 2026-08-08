from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_peer")).items() if not k.startswith("__")})

class TestAnImpossibleRecordIsSetAsideRatherThanPlayed:
    def a_turn(self, **changed: object) -> TurnMessage:
        body: dict[str, Any] = {
            "step": 1,
            "sender": "thief",
            "hint": "",
            "smell_grid": {},
            "commit": OTHER,
            "timestamp": WHEN,
            "game_uid": "series-123",
            "sub_game": 2,
        }
        body.update(changed)
        return TurnMessage(**body)
    def test_a_foreign_commitment_does_not_strand_the_legitimate_one_behind_it(self) -> None:
        peer, _, inboxes = a_peer(timeout=2.0)
        inboxes.turns.put(self.a_turn(game_uid="old-or-forged", commit=DIGEST))
        inboxes.turns.put(self.a_turn())
        assert peer.await_commit(1).commit == OTHER
        assert [record["game_uid"] for record in peer.quarantined] == ["old-or-forged"]
    def test_a_commitment_for_a_sub_game_we_are_not_playing_is_skipped_too(self) -> None:
        peer, _, inboxes = a_peer(timeout=2.0)
        inboxes.turns.put(self.a_turn(sub_game=1, commit=DIGEST))
        inboxes.turns.put(self.a_turn())
        assert peer.await_commit(1).commit == OTHER
    def test_nothing_but_foreign_commitments_still_ends_on_the_deadline(self) -> None:
        peer, _, inboxes = a_peer()
        inboxes.turns.put(self.a_turn(game_uid="old-or-forged"))
        with pytest.raises(PeerTimeout, match="commitment for step 1"):
            peer.await_commit(1)
    def an_audit(self, records: list[dict[str, Any]], **changed: object) -> AuditPayload:
        body: dict[str, Any] = {
            "sender": "thief",
            "records": records,
            "result_claim": UNDECIDED,
            "game_uid": "series-123",
            "sub_game": 2,
        }
        body.update(changed)
        return AuditPayload(**body)
    def test_a_foreign_audit_payload_does_not_strand_the_reveal_behind_it(self) -> None:
        peer, _, inboxes = a_peer(timeout=2.0)
        forged = Reveal(step=1, sender="thief", move="S", intent="truth", hint="a", timestamp=WHEN)
        wanted = Reveal(step=1, sender="thief", move="N", intent="truth", hint="b", timestamp=WHEN)
        inboxes.audits.put(self.an_audit([forged.to_dict()], game_uid="old-or-forged"))
        inboxes.audits.put(self.an_audit([wanted.to_dict()]))
        assert peer.await_reveal(1).move == "N"
        assert peer.quarantined == [forged.to_dict()]
    def test_a_record_re_wrapped_in_a_matching_envelope_is_skipped_by_its_own_binding(
        self,
    ) -> None:
        peer, _, inboxes = a_peer(timeout=2.0)
        forged = Reveal(
            step=1,
            sender="thief",
            move="S",
            intent="truth",
            hint="no",
            timestamp=WHEN,
            game_uid="old-or-forged",
        )
        wanted = Reveal(step=1, sender="thief", move="N", intent="truth", hint="b", timestamp=WHEN)
        inboxes.audits.put(self.an_audit([forged.to_dict(), wanted.to_dict()]))
        assert peer.await_reveal(1).move == "N"
        assert peer.quarantined == [forged.to_dict()]
    def test_two_reveals_for_one_step_that_disagree_are_refused_rather_than_ranked(self) -> None:
        peer, _, inboxes = a_peer(timeout=2.0)
        one = Reveal(step=1, sender="thief", move="S", intent="truth", hint="a", timestamp=WHEN)
        two = Reveal(step=1, sender="thief", move="N", intent="truth", hint="b", timestamp=WHEN)
        inboxes.audits.put(self.an_audit([one.to_dict(), two.to_dict()]))
        with pytest.raises(CeremonyError, match="conflicting reveals for step 1"):
            peer.await_reveal(1)
    def test_nothing_but_foreign_payloads_still_ends_on_the_deadline(self) -> None:
        peer, _, inboxes = a_peer()
        stray = Reveal(step=1, sender="thief", move="S", intent="truth", hint="t", timestamp=WHEN)
        inboxes.audits.put(self.an_audit([stray.to_dict()], sub_game=1))
        with pytest.raises(PeerTimeout, match="audit record"):
            peer.await_reveal(1)
