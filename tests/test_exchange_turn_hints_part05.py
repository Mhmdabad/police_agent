from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_exchange_turn_hints")).items() if not k.startswith("__")})

@pytest.mark.parametrize(
    "hint",
    [
        "I moved north last turn",
        "I am nowhere near the bridge",
        "There are 3 bridges north of here",
        "My xylophone has 3 strings",
        "Rowboats and columns line the old hall",
    ],
)
def test_benign_deceptive_and_non_coordinate_hints_are_not_overblocked(hint: str) -> None:
    assert Reveal.from_dict(reveal(hint=hint)).hint == hint
