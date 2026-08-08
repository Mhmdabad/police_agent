from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_config")).items() if not k.startswith("__")})

class TestNegotiable:
    @pytest.mark.parametrize(
        ("section", "key", "value"),
        [
            ("world", "map_area", "London"),
            ("world", "hint_max_words", 8),
            ("board_and_agents", "axis_origin_corner", "bottom-right"),
            ("board_and_agents", "axis_start_index", 1),
            ("network_and_league", "response_timeout_sec", 5),
        ],
    )
    def test_any_agreed_value_passes(self, section: str, key: str, value: object) -> None:
        config = copy.deepcopy(shipped())
        config[section][key] = value
        validate(config)
