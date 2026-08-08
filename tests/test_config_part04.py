from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_config")).items() if not k.startswith("__")})

class TestMinimums:
    @pytest.mark.parametrize(
        ("section", "key", "below"),
        [
            ("board_and_agents", "grid_size", 5),
            ("movement_and_barriers", "max_barriers", 10),
            ("movement_and_barriers", "survival_threshold", 20),
            ("rate_limiter_gatekeeper", "max_retries", 1),
        ],
    )
    def test_below_the_book_value_is_refused(self, section: str, key: str, below: int) -> None:
        config = copy.deepcopy(shipped())
        config[section][key] = below
        with pytest.raises(ConfigError, match="never lowered"):
            validate(config)
    @pytest.mark.parametrize(
        ("section", "key", "above"),
        [
            ("board_and_agents", "grid_size", 10),
            ("movement_and_barriers", "max_barriers", 20),
            ("movement_and_barriers", "survival_threshold", 50),
        ],
    )
    def test_raising_is_allowed(self, section: str, key: str, above: int) -> None:
        config = copy.deepcopy(shipped())
        config[section][key] = above
        validate(config)
