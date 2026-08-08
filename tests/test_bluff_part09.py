from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_bluff")).items() if not k.startswith("__")})

class TestTheFlagIsValidatedOnTheObjectToo:
    def test_a_bluff_cannot_be_built_with_a_bad_intent(self) -> None:
        with pytest.raises(ValueError, match="intent must be one of"):
            Bluff(intent="perhaps", text="north", about=(0, 0))
    def test_a_valid_one_is_immutable(self) -> None:
        spoken = Bluff(intent="lie", text="north", about=(0, 0))
        with pytest.raises(AttributeError):
            spoken.intent = "truth"  # type: ignore[misc]
