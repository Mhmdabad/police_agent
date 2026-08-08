from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_exchange_turn_hints")).items() if not k.startswith("__")})

@pytest.mark.parametrize(
    "changes, detail",
    [
        ({"hint": None}, "must be a string"),
        ({"hint": ""}, "must not be empty"),
        ({"hint": "   \t"}, "must not be blank"),
        (
            {
                "hint": "one two three four five six seven eight "
                "nine ten eleven twelve thirteen fourteen fifteen sixteen"
            },
            "over 15 words",
        ),
        ({"hint": "safe\nlooking"}, "control character"),
        ({"hint": "bad\ud800text"}, "Unicode scalar"),
        ({"hint": "safe\u202elooking"}, "format character"),
        ({"hint": "I am at 3,4"}, "numeric coordinates"),
        ({"hint": "Next turn I will move north"}, "future action"),
        ({"hint": "I intend to move north next turn"}, "future action"),
        ({"hint": "I’ll move north"}, "future action"),
        ({"hint": "I'll move north"}, "future action"),
        ({"hint": "I will move north"}, "future action"),
        ({"hint": "coordinates 3 and 4"}, "numeric coordinates"),
        ({"hint": "x=3 y=4"}, "numeric coordinates"),
        ({"hint": "ROW : 3; COLUMN = 4"}, "numeric coordinates"),
    ],
)
def test_wire_refuses_malformed_or_oversized_hints(changes: dict[str, object], detail: str) -> None:
    with pytest.raises(CeremonyError, match=detail):
        Reveal.from_dict(reveal(**changes))
