from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_quota")).items() if not k.startswith("__")})

class TestTheDefaultCeiling:
    def test_it_is_well_below_anything_google_enforces(self) -> None:
        assert DAILY_LIMIT == 50
        assert DAILY_LIMIT < 500, "the free-tier recipient limit is an order of magnitude up"
    def test_it_leaves_room_for_the_league(self) -> None:
        assert DAILY_LIMIT > 10 * 2
    def test_the_default_is_used_when_no_limit_is_given(self, tmp_path: Path) -> None:
        assert Quota(path=tmp_path / "q.json").limit == DAILY_LIMIT
