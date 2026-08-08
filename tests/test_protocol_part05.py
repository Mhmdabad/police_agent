from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_protocol")).items() if not k.startswith("__")})

class TestInboxes:
    def test_a_valid_turn_is_queued_and_acked(self) -> None:
        boxes = PeerInboxes(game_uid="series-123", sub_game=2)
        assert boxes.receive_turn(TURN) == ACK
        assert boxes.turns.get_nowait().step == 3
    def test_a_malformed_turn_is_refused_not_queued(self) -> None:
        boxes = PeerInboxes(game_uid="series-123", sub_game=2)
        result = boxes.receive_turn({"sender": "police"})
        assert result["ok"] is False
        assert boxes.turns.empty()
    def test_a_refusal_is_recorded_for_the_dispute(self) -> None:
        boxes = PeerInboxes(game_uid="series-123", sub_game=2)
        boxes.receive_turn(None)
        assert boxes.rejected and "receive_turn" in boxes.rejected[0]
    def test_nothing_raises_across_the_wire(self) -> None:
        boxes = PeerInboxes(game_uid="series-123", sub_game=2)
        hostiles: tuple[object, ...] = (None, [], "x", 1, {"sender": "referee"})
        for hostile in hostiles:
            assert boxes.negotiate(hostile)["ok"] in (True, False)
            assert boxes.receive_turn(hostile)["ok"] is False
            assert boxes.submit_audit(hostile)["ok"] is False
            assert boxes.receive_control(hostile)["ok"] is False
    def test_agreements_audits_and_controls_queue_separately(self) -> None:
        boxes = PeerInboxes(game_uid="series-123", sub_game=1)
        boxes.negotiate({"terms": {}})
        boxes.submit_audit(
            {
                "sender": "police",
                "records": [],
                "result_claim": "capture",
                "game_uid": "series-123",
                "sub_game": 1,
            }
        )
        boxes.receive_control({"kind": "enable", "sender": "police"})
        assert boxes.agreements.qsize() == 1
        assert boxes.audits.qsize() == 1
        assert boxes.controls.qsize() == 1
        assert boxes.turns.empty()
    def test_accepting_a_message_does_not_block_on_our_runtime(self) -> None:
        boxes = PeerInboxes(game_uid="series-123", sub_game=2)
        for step in range(100):
            assert boxes.receive_turn({**TURN, "step": step}) == ACK
        assert boxes.turns.qsize() == 100
