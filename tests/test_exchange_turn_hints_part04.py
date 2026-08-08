from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_exchange_turn_hints")).items() if not k.startswith("__")})

def test_wire_accepts_exactly_the_word_limit() -> None:
    text = " ".join(["שלום"] * 15)
    assert Reveal.from_dict(reveal(hint=text)).hint == text
