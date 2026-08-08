from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_series_length")).items() if not k.startswith("__")})

class TestTheShippedConfigIsASixSubGameSeries:
    def test_it_says_six(self) -> None:
        assert shipped()[SERIES_SECTION][SERIES_KEY] == BOOK_SERIES
    def test_it_validates(self) -> None:
        validate(shipped())
    def test_the_series_length_read_back_out_of_it_is_six(self) -> None:
        assert series_length(shipped()) == BOOK_SERIES
    def test_the_negotiated_terms_carry_six(self) -> None:
        assert to_terms(shipped())[SERIES_KEY] == BOOK_SERIES
    def test_the_terms_fallback_is_the_book_value_not_one(self) -> None:
        config = copy.deepcopy(shipped())
        del config[SERIES_SECTION]
        assert to_terms(config)[SERIES_KEY] == BOOK_SERIES
