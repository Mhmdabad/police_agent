from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_config")).items() if not k.startswith("__")})

class TestReporting:
    def test_missing_parameter_is_reported(self) -> None:
        config = copy.deepcopy(shipped())
        del config["scoring"]["capture_cop"]
        with pytest.raises(ConfigError, match="scoring.capture_cop is missing"):
            validate(config)
    def test_missing_section_is_reported(self) -> None:
        config = copy.deepcopy(shipped())
        del config["pheromones"]
        with pytest.raises(ConfigError, match="pheromones.pheromone_decay is missing"):
            validate(config)
    def test_all_violations_are_listed_not_just_the_first(self) -> None:
        config = copy.deepcopy(shipped())
        config["scoring"]["capture_cop"] = 99
        config["scoring"]["survival_thief"] = 1
        config["board_and_agents"]["grid_size"] = 3
        with pytest.raises(ConfigError) as excinfo:
            validate(config)
        message = str(excinfo.value)
        assert "scoring.capture_cop" in message
        assert "scoring.survival_thief" in message
        assert "board_and_agents.grid_size" in message
