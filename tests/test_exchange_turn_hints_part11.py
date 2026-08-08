from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_exchange_turn_hints")).items() if not k.startswith("__")})

class TestNothingReachesAQueueBeforeTheDoorIsBound:
    def test_a_forged_packet_before_binding_is_refused_and_leaves_no_trace(self) -> None:
        inboxes = PeerInboxes()
        answer = inboxes.receive_turn(turn(game_uid="old-or-forged", sub_game=1))
        assert deferred(answer)
        assert inboxes.turns.empty()
        assert inboxes.accepted_turns == {}
        assert inboxes.duplicates == [] and inboxes.rejected == []
        assert len(inboxes.deferred) == 1
    def test_the_same_forgery_after_binding_is_refused_for_good(self) -> None:
        inboxes = PeerInboxes()
        inboxes.bind("series-123", 1)
        answer = inboxes.receive_turn(turn(game_uid="old-or-forged", sub_game=1))
        assert answer["ok"] is False and answer.get(RETRY_KEY) is not True
        assert "old-or-forged" in str(answer["detail"])
        assert inboxes.turns.empty() and inboxes.accepted_turns == {}
        assert len(inboxes.rejected) == 1
    def test_a_forgery_before_the_bind_cannot_poison_the_head_of_the_queue(self) -> None:
        inboxes = PeerInboxes()
        assert deferred(inboxes.receive_turn(turn(game_uid="old-or-forged", sub_game=1)))
        inboxes.bind("series-123", 1)
        assert inboxes.receive_turn(turn(sub_game=1)) == {"ok": True}
        assert inboxes.turns.qsize() == 1
        queued = inboxes.turns.get_nowait()
        assert (queued.game_uid, queued.sub_game) == ("series-123", 1)
        assert list(inboxes.accepted_turns) == [(OPPONENT, 1, "series-123", 1)]
    def test_an_honest_packet_that_beat_the_bind_is_deferred_then_accepted(self) -> None:
        inboxes = PeerInboxes()
        assert deferred(inboxes.receive_turn(turn(sub_game=1)))
        assert inboxes.turns.empty() and inboxes.accepted_turns == {}
        inboxes.bind("series-123", 1)
        assert inboxes.receive_turn(turn(sub_game=1)) == {"ok": True}
        assert inboxes.turns.get_nowait().sub_game == 1
        assert inboxes.rejected == [] and inboxes.duplicates == []
    def test_the_audit_door_is_shut_before_binding_too(self) -> None:
        inboxes = PeerInboxes()
        assert deferred(inboxes.submit_audit(audit([reveal(sub_game=1)], sub_game=1)))
        assert inboxes.audits.empty()
        assert inboxes.accepted_reveals == {}
        assert inboxes.rejected == []
    def test_a_sub_game_this_series_has_not_opened_is_deferred_not_queued(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=3)
        assert deferred(inboxes.receive_turn(turn(sub_game=4)))
        assert inboxes.turns.empty() and inboxes.accepted_turns == {}
        assert inboxes.rejected == []
    def test_and_the_re_send_lands_once_we_have_crossed_too(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=3)
        assert deferred(inboxes.receive_turn(turn(sub_game=4)))
        inboxes.bind("series-123", 4)
        assert inboxes.receive_turn(turn(sub_game=4)) == {"ok": True}
        assert inboxes.submit_audit(audit([reveal(sub_game=4)], sub_game=4)) == {"ok": True}
        assert inboxes.rejected == []
    def test_binding_takes_the_series_before_it_takes_the_sub_game(self) -> None:
        inboxes = PeerInboxes()
        seen: list[tuple[str, int]] = []
        original = PeerInboxes.receive_turn
        def watching(self: PeerInboxes, message: object) -> dict[str, object]:
            seen.append((self.game_uid, self.sub_game))
            return original(self, message)
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(PeerInboxes, "receive_turn", watching)
            inboxes.bind("series-123", 1)
            assert deferred(inboxes.receive_turn(turn(game_uid="series-123", sub_game=2)))
        assert seen == [("series-123", 1)]
    def test_a_greeting_does_not_forget_a_turn_it_arrived_after(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=2)
        assert inboxes.receive_turn(turn()) == {"ok": True}
        inboxes.negotiate({"greeting": {"role": OPPONENT, "public_url": "https://moved"}})
        assert inboxes.submit_audit(audit([reveal()])) == {"ok": True}
        assert inboxes.rejected == []
    def test_step_one_recurs_every_sub_game_without_looking_like_a_replay(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=1)
        for number in range(1, 7):
            inboxes.bind("series-123", number)
            assert inboxes.receive_turn(turn(sub_game=number)) == {"ok": True}
        assert inboxes.rejected == [] and inboxes.duplicates == []
        assert len(inboxes.accepted_turns) == 6
