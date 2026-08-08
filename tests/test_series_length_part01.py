from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_series_length")).items() if not k.startswith("__")})

class TestTheBindingTableCarriesTheRow:
    def test_the_row_is_present_with_the_book_key_value_and_status(self) -> None:
        assert Param(SERIES_SECTION, SERIES_KEY, BOOK_SERIES, Status.FIXED) in TABLE
    def test_it_is_named_by_the_key_the_shared_config_uses(self) -> None:
        assert (SERIES_SECTION, SERIES_KEY) == ("network_and_league", "num_games")
    def test_it_is_readable_through_the_accessor_like_every_other_parameter(self) -> None:
        assert book_int(SERIES_SECTION, SERIES_KEY) == BOOK_SERIES
    def test_it_is_fixed_rather_than_a_minimum_or_negotiable(self) -> None:
        row = next(p for p in TABLE if (p.section, p.key) == (SERIES_SECTION, SERIES_KEY))
        assert row.status is Status.FIXED
