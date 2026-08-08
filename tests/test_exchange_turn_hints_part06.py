from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_exchange_turn_hints")).items() if not k.startswith("__")})

def test_unbound_legacy_reveal_fails_closed() -> None:
    legacy = reveal()
    legacy.pop("game_uid")
    legacy.pop("sub_game")
    with pytest.raises(CeremonyError, match="game_uid"):
        Reveal.from_dict(legacy)
