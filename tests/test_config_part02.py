from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_config")).items() if not k.startswith("__")})

class TestShippedConfig:
    def test_validates_clean(self) -> None:
        validate(shipped())
    def test_loads(self) -> None:
        assert load(CONFIG_PATH)["schema_version"] in ("1.2", "1.3")
