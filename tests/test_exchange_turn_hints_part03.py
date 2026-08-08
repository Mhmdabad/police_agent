from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_exchange_turn_hints")).items() if not k.startswith("__")})

def test_wire_preserves_unicode_hint_exactly_and_does_not_confuse_it_with_scent() -> None:
    text = "אני ליד הגשר — maybe"
    opened = Reveal.from_dict(reveal(hint=text, scent={"3,3": 0.9}))
    assert opened.hint == text
    assert opened.intent == "lie"
    assert opened.scent == {"3,3": 0.9}
