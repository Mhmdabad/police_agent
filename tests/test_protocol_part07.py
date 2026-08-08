from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_protocol")).items() if not k.startswith("__")})

class TestARetriedTurnIsNotASecondTurn:
    def test_the_first_copy_is_taken(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=2)
        assert inboxes.receive_turn(TURN) == ACK
        assert inboxes.turns.qsize() == 1
    def test_an_identical_re_send_is_acknowledged_and_dropped(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=2)
        inboxes.receive_turn(TURN)
        assert inboxes.receive_turn(dict(TURN)) == ACK
        assert inboxes.turns.qsize() == 1
        assert inboxes.duplicates == ["receive_turn: police step 3 re-sent"]
    def test_key_order_does_not_make_a_re_send_look_new(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=2)
        inboxes.receive_turn(TURN)
        inboxes.receive_turn(dict(reversed(list(TURN.items()))))
        assert inboxes.turns.qsize() == 1
    def test_the_same_step_with_a_different_move_is_refused(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=2)
        inboxes.receive_turn(TURN)
        reply = inboxes.receive_turn({**TURN, "commit": "b" * 64})
        assert reply["ok"] is False
        assert "never replace one" in reply["detail"]
        assert inboxes.turns.qsize() == 1
    def test_the_contradiction_is_recorded_not_only_refused(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=2)
        inboxes.receive_turn(TURN)
        inboxes.receive_turn({**TURN, "hint": "a different story"})
        assert any("already played step 3" in entry for entry in inboxes.rejected)
    def test_a_later_step_is_not_a_duplicate(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=2)
        inboxes.receive_turn(TURN)
        inboxes.receive_turn({**TURN, "step": 4})
        assert inboxes.turns.qsize() == 2
    def test_each_sender_has_its_own_step_numbering(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=2)
        inboxes.receive_turn(TURN)
        inboxes.receive_turn({**TURN, "sender": "thief"})
        assert inboxes.turns.qsize() == 2
    def test_a_malformed_turn_is_not_remembered(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=2)
        inboxes.receive_turn({**TURN, "commit": 42})
        assert inboxes.receive_turn(TURN) == ACK
        assert inboxes.turns.qsize() == 1
    def test_greetings_are_deliberately_not_deduplicated(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=2)
        inboxes.negotiate({"greeting": {"public_url": "https://a"}})
        inboxes.negotiate({"greeting": {"public_url": "https://a"}})
        assert inboxes.agreements.qsize() == 2
