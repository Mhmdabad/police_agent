from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_series_length")).items() if not k.startswith("__")})

class TestValidationRefusesAnyOtherSeriesLength:
    @pytest.mark.parametrize(
        "bad",
        [1, 5, 7, 0, -6, 12, True, False, 6.0, 5.9, "6", "six", None, [6], {"num_games": 6}],
        ids=[
            "one",
            "five",
            "seven",
            "zero",
            "negative",
            "twelve",
            "true",
            "false",
            "float-six",
            "float",
            "string-six",
            "word",
            "null",
            "list",
            "nested-dict",
        ],
    )
    def test_a_deviation_is_refused_whatever_it_is_dressed_as(self, bad: object) -> None:
        config = copy.deepcopy(shipped())
        config[SERIES_SECTION][SERIES_KEY] = bad
        with pytest.raises(ConfigError, match="disqualifies the team"):
            validate(config)
    def test_the_complaint_names_the_parameter_and_the_book_value(self) -> None:
        config = copy.deepcopy(shipped())
        config[SERIES_SECTION][SERIES_KEY] = 1
        with pytest.raises(ConfigError) as excinfo:
            validate(config)
        assert "network_and_league.num_games" in str(excinfo.value)
        assert "6" in str(excinfo.value)
    def test_a_missing_value_is_reported_rather_than_defaulted(self) -> None:
        config = copy.deepcopy(shipped())
        del config[SERIES_SECTION][SERIES_KEY]
        with pytest.raises(ConfigError, match="network_and_league.num_games is missing"):
            validate(config)
    def test_a_missing_section_is_reported(self) -> None:
        config = copy.deepcopy(shipped())
        del config[SERIES_SECTION]
        with pytest.raises(ConfigError, match="network_and_league.num_games is missing"):
            validate(config)
    @pytest.mark.parametrize("instead", [6, "six", [{"num_games": 6}], None])
    def test_a_section_that_is_not_a_section_is_reported(self, instead: object) -> None:
        config = copy.deepcopy(shipped())
        config[SERIES_SECTION] = instead
        with pytest.raises(ConfigError, match="network_and_league.num_games is missing"):
            validate(config)
    def test_the_value_must_be_where_the_schema_puts_it(self) -> None:
        config = copy.deepcopy(shipped())
        del config[SERIES_SECTION][SERIES_KEY]
        config[SERIES_SECTION]["league"] = {SERIES_KEY: BOOK_SERIES}
        config[SERIES_KEY] = BOOK_SERIES
        with pytest.raises(ConfigError, match="network_and_league.num_games is missing"):
            validate(config)
    def test_the_book_value_itself_passes(self) -> None:
        config = copy.deepcopy(shipped())
        config[SERIES_SECTION][SERIES_KEY] = BOOK_SERIES
        validate(config)
