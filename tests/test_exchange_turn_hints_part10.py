from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_exchange_turn_hints")).items() if not k.startswith("__")})

def test_reveal_from_prior_sub_game_is_rejected_before_current_one_is_queued() -> None:
    inboxes = PeerInboxes(game_uid="series-123", sub_game=2)
    inboxes.receive_turn(
        {
            "step": 1,
            "sender": "thief",
            "hint": "",
            "smell_grid": {},
            "commit": "a" * 64,
            "timestamp": "now",
            "game_uid": "series-123",
            "sub_game": 2,
        }
    )
    old = {
        "sender": "thief",
        "records": [reveal()],
        "result_claim": "in_progress",
        "game_uid": "series-123",
        "sub_game": 1,
    }
    current = {**old, "sub_game": 2}
    assert inboxes.submit_audit(old)["ok"] is False
    assert inboxes.audits.empty()
    assert inboxes.submit_audit(current) == {"ok": True}
    assert inboxes.audits.get_nowait().sub_game == 2
