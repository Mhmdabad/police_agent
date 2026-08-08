from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_actions")).items() if not k.startswith("__")})

class TestExhaustiveness:
    def test_dispatch_is_statically_exhaustive(self) -> None:
        foreign = typing.cast(Action, object())
        with pytest.raises(AssertionError):
            apply_action(make(), "cop", foreign, AXES)
