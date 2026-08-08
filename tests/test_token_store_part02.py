from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_store")).items() if not k.startswith("__")})

class TestAGoodTokenLoads:
    def test_it_returns_the_refresh_token_and_scopes(self, tmp_path: Path) -> None:
        token = read(stored(tmp_path), CLIENT)
        assert token.refresh_token == GOOD["refresh_token"]
        assert token.scopes == (SEND_SCOPE,)
    def test_a_future_expiry_is_not_expired(self, tmp_path: Path) -> None:
        assert not read(stored(tmp_path), CLIENT).expired
    def test_a_past_expiry_is_expired_and_that_is_fine(self, tmp_path: Path) -> None:
        past = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
        token = read(stored(tmp_path, expiry=past), CLIENT)
        assert token.expired
        assert token.refresh_token
    def test_a_naive_expiry_is_read_as_utc(self, tmp_path: Path) -> None:
        assert not read(stored(tmp_path, expiry="2099-01-01T00:00:00"), CLIENT).expired
    @pytest.mark.parametrize("value", ["not a date", 17, None])
    def test_an_unreadable_expiry_is_unknown_rather_than_fatal(
        self, tmp_path: Path, value: object
    ) -> None:
        token = read(stored(tmp_path, expiry=value), CLIENT)
        assert token.expiry is None
        assert not token.expired
    def test_the_summary_does_not_contain_the_refresh_token(self, tmp_path: Path) -> None:
        token = read(stored(tmp_path), CLIENT)
        assert GOOD["refresh_token"] not in token.summary
        assert "current" in token.summary
