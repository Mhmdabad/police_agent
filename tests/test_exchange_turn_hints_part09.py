from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_exchange_turn_hints")).items() if not k.startswith("__")})

def test_reveal_retry_is_idempotent_but_cannot_mask_a_conflicting_hint() -> None:
    inboxes = PeerInboxes(game_uid="series-123", sub_game=2)
    committed = {
        "step": 1,
        "sender": "thief",
        "hint": "",
        "smell_grid": {},
        "commit": "a" * 64,
        "timestamp": "now",
        "game_uid": "series-123",
        "sub_game": 2,
        "barrier_placed": None,
        "capture_claim": None,
        "claim_response": None,
        "win_claim": None,
    }
    assert inboxes.receive_turn(committed) == {"ok": True}
    payload = {
        "sender": "thief",
        "records": [reveal()],
        "result_claim": "in_progress",
        "game_uid": "series-123",
        "sub_game": 2,
    }
    assert inboxes.submit_audit(payload) == {"ok": True}
    assert inboxes.submit_audit(payload) == {"ok": True}
    conflicting = {
        "sender": "thief",
        "records": [reveal(hint="a different story")],
        "result_claim": "in_progress",
        "game_uid": "series-123",
        "sub_game": 2,
    }
    answer = inboxes.submit_audit(conflicting)
    assert answer["ok"] is False
    assert "revealed step 1 differently" in answer["detail"]
    assert inboxes.audits.qsize() == 1
