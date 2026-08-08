from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_exchange_turn_hints")).items() if not k.startswith("__")})

def test_inner_binding_mutated_to_current_has_no_effect_without_current_phase_one() -> None:
    inboxes = PeerInboxes(game_uid="series-123", sub_game=2)
    payload = {
        "sender": "thief",
        "records": [reveal()],
        "result_claim": "in_progress",
        "game_uid": "series-123",
        "sub_game": 2,
    }
    answer = inboxes.submit_audit(payload)
    assert answer["ok"] is False
    assert "without a current phase-one commitment" in answer["detail"]
    assert inboxes.audits.empty()
