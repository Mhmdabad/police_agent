from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_strategy")).items() if not k.startswith("__")})

class TestContract:
    def test_the_role_is_the_cop(self) -> None:
        assert PoliceBrain(axes=AXES).role == "cop"
    def test_options_are_in_stable_order(self) -> None:
        brain = PoliceBrain(axes=AXES)
        state = make(cop=(3, 3))
        assert brain.options(state) == list(MOVES)
    def test_the_base_class_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            BrainBase()  # type: ignore[abstract]
