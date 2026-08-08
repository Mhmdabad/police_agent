from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_exchange_turn_hints")).items() if not k.startswith("__")})

def test_rewrapped_old_reveal_is_rejected_by_its_immutable_inner_binding() -> None:
    inboxes = PeerInboxes(game_uid="series-123", sub_game=2)
    assert (
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
        )["ok"]
        is True
    )
    payload = {
        "sender": "thief",
        "records": [reveal(sub_game=1)],
        "result_claim": "in_progress",
        "game_uid": "series-123",
        "sub_game": 2,
    }
    assert inboxes.submit_audit(payload)["ok"] is False
    assert inboxes.audits.empty()
    payload["records"] = [reveal(game_uid="other-series")]
    assert inboxes.submit_audit(payload)["ok"] is False
    assert inboxes.audits.empty()
