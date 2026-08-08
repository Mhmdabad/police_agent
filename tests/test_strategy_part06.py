from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_strategy")).items() if not k.startswith("__")})

class TestLoader:
    def test_an_absent_section_loads_the_shipped_brain(self) -> None:
        assert isinstance(load_brain(None), PoliceBrain)
    def test_an_empty_section_loads_the_shipped_brain(self) -> None:
        assert isinstance(load_brain({}), PoliceBrain)
    def test_the_default_reference_resolves(self) -> None:
        assert isinstance(load_brain({"police_class": DEFAULT_BRAIN}), PoliceBrain)
    def test_a_custom_brain_is_loaded(self) -> None:
        spec = "cop_agent.strategy.police_brain:PoliceBrain"
        assert isinstance(load_brain({"police_class": spec}), BrainBase)
    def test_a_malformed_reference_is_refused(self) -> None:
        with pytest.raises(StrategyError, match="package.module:Class"):
            load_brain({"police_class": "not_a_reference"})
    def test_an_unimportable_module_is_refused(self) -> None:
        with pytest.raises(StrategyError, match="cannot import"):
            load_brain({"police_class": "no.such.module:Brain"})
    def test_a_missing_class_is_refused(self) -> None:
        with pytest.raises(StrategyError, match="has no"):
            load_brain({"police_class": "cop_agent.strategy.police_brain:Missing"})
    def test_a_non_brain_is_refused(self) -> None:
        with pytest.raises(StrategyError, match="does not subclass"):
            load_brain({"police_class": "cop_agent.strategy.police_brain:manhattan"})
    def test_the_axis_convention_is_threaded_through(self) -> None:
        flipped = AxisConvention(origin_corner="bottom-right")
        assert load_brain({}, axes=flipped).axes == flipped
    def test_the_seed_is_threaded_through(self) -> None:
        assert load_brain({}, seed=42).seed == 42
    def test_the_shipped_private_config_selects_the_default(self) -> None:
        path = Path(__file__).parents[1] / "config/police/game.toml"
        private: dict[str, Any] = tomllib.loads(path.read_text())
        assert isinstance(load_brain(private.get("strategy")), PoliceBrain)
