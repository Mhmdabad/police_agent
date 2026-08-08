from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_strategy")).items() if not k.startswith("__")})

class TestDecision:
    def test_carries_an_action(self) -> None:
        assert isinstance(PoliceBrain(axes=AXES).decide(make()), Decision)
    def test_defaults_to_a_truthful_intent(self) -> None:
        assert PoliceBrain(axes=AXES).decide(make()).intent == "truth"
