from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_store")).items() if not k.startswith("__")})

class TestTheStoredTokenObject:
    def test_a_token_with_no_expiry_is_not_expired(self) -> None:
        token = StoredToken(client_id=CLIENT, refresh_token="r", scopes=(SEND_SCOPE,))
        assert not token.expired
        assert "current" in token.summary
    def test_an_expired_token_says_so_in_its_summary(self) -> None:
        token = StoredToken(
            client_id=CLIENT,
            refresh_token="r",
            scopes=(SEND_SCOPE,),
            expiry=datetime(2000, 1, 1, tzinfo=UTC),
        )
        assert "expired" in token.summary
