from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_config")).items() if not k.startswith("__")})

class TestFixedValues:
    @pytest.mark.parametrize(
        ("section", "key", "bad"),
        [
            ("scoring", "capture_cop", 99),
            ("scoring", "tie_score", 3),
            ("pheromones", "pheromone_decay", 0.2),
            ("board_and_agents", "num_agents", 3),
            ("network_and_league", "diversity_reward", 20),
        ],
    )
    def test_any_deviation_is_refused(self, section: str, key: str, bad: object) -> None:
        config = copy.deepcopy(shipped())
        config[section][key] = bad
        with pytest.raises(ConfigError, match="disqualifies the team"):
            validate(config)
    def test_move_set_may_not_gain_a_diagonal(self) -> None:
        config = copy.deepcopy(shipped())
        config["movement_and_barriers"]["move_set"].append("NE")
        with pytest.raises(ConfigError, match="disqualifies the team"):
            validate(config)
