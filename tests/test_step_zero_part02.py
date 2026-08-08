from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_step_zero")).items() if not k.startswith("__")})

class TestFieldsAreNamedForWhatTheyActuallyMeasure:
    def test_cores_are_named_logical_because_that_is_what_is_counted(self) -> None:
        assert "logical_cores" in collect("m", environ={}).to_dict()
        assert "cpu_cores" not in collect("m", environ={}).to_dict()
    def test_the_declared_model_comes_from_config_not_from_the_environment(self) -> None:
        assert collect("claude-haiku-4-5", environ={}).llm_model == "claude-haiku-4-5"
