from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_series_length")).items() if not k.startswith("__")})

class TestTheSeriesLengthComesFromTheValidatedConfig:
    def test_a_valid_config_yields_the_book_length(self) -> None:
        assert series_length(shipped()) == BOOK_SERIES
    def test_an_invalid_config_yields_nothing_at_all(self) -> None:
        config = copy.deepcopy(shipped())
        config[SERIES_SECTION][SERIES_KEY] = 1
        with pytest.raises(ConfigError, match="disqualifies the team"):
            series_length(config)
    def test_a_deviation_anywhere_in_the_config_still_refuses(self) -> None:
        config = copy.deepcopy(shipped())
        config["scoring"]["capture_cop"] = 99
        with pytest.raises(ConfigError, match="disqualifies the team"):
            series_length(config)
    def test_asking_for_the_book_length_is_allowed(self) -> None:
        assert series_length(shipped(), requested=BOOK_SERIES) == BOOK_SERIES
    @pytest.mark.parametrize("requested", [1, 3, 5, 7, 0])
    def test_asking_for_anything_else_is_refused(self, requested: int) -> None:
        with pytest.raises(ConfigError, match="disqualifies the team"):
            series_length(shipped(), requested=requested)
    def test_the_refusal_names_the_table_row(self) -> None:
        with pytest.raises(ConfigError) as excinfo:
            series_length(shipped(), requested=1)
        assert "Appendix F" in str(excinfo.value)
        assert "table 18" in str(excinfo.value)
    def test_the_length_is_an_integer_not_a_boolean(self) -> None:
        length = series_length(shipped())
        assert isinstance(length, int) and not isinstance(length, bool)
