from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_exchange_turn_hints")).items() if not k.startswith("__")})

class TestWhatIsBehindUsIsStillRefused:
    def test_a_turn_from_a_sub_game_already_played_is_refused(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=4)
        answer = inboxes.receive_turn(turn(sub_game=3))
        assert answer["ok"] is False and "already past" in answer["detail"]
        assert inboxes.turns.empty()
    def test_a_turn_from_another_series_is_refused_however_far_along_it_is(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=2)
        answer = inboxes.receive_turn(turn(game_uid="series-999", sub_game=6))
        assert answer["ok"] is False and "series 'series-999'" in answer["detail"]
        assert inboxes.turns.empty()
    def test_a_reveal_rewrapped_in_a_fresher_envelope_is_refused(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=2)
        inboxes.receive_turn(turn())
        answer = inboxes.submit_audit(audit([reveal(sub_game=1)]))
        assert answer["ok"] is False and "travelled in an audit for" in answer["detail"]
        assert inboxes.audits.empty()
    def test_a_retry_of_an_accepted_turn_is_a_duplicate_not_a_second_turn(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=4)
        assert inboxes.receive_turn(turn(sub_game=4)) == {"ok": True}
        assert inboxes.receive_turn(turn(sub_game=4)) == {"ok": True}
        assert inboxes.turns.qsize() == 1
        assert len(inboxes.duplicates) == 1 and inboxes.rejected == []
    def test_a_deferred_turn_leaves_nothing_for_its_re_send_to_collide_with(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=3)
        for _ in range(3):
            assert deferred(inboxes.receive_turn(turn(sub_game=4)))
        inboxes.bind("series-123", 4)
        assert inboxes.receive_turn(turn(sub_game=4)) == {"ok": True}
        assert inboxes.duplicates == [] and inboxes.turns.qsize() == 1
    def test_a_turn_changed_after_the_fact_is_still_a_forgery(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=4)
        inboxes.receive_turn(turn(sub_game=4))
        answer = inboxes.receive_turn(turn(sub_game=4, commit="b" * 64))
        assert answer["ok"] is False and "never replace one" in answer["detail"]
