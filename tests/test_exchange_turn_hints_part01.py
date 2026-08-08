from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_exchange_turn_hints")).items() if not k.startswith("__")})

def test_default_brain_emits_one_safe_hint_even_when_staying() -> None:
    state = BoardState(cop=(0, 0), thief=(3, 3), grid_size=7)
    decision = StayingBrain().decide(state)
    assert decision == Decision(
        action=MoveAction("STAY"),
        hint="I am watching the streets",
        intent="truth",
    )
