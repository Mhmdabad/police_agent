from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_authorize")).items() if not k.startswith("__")})

class TestWhatComesBackIsJudgedToo:
    def test_an_over_scoped_grant_is_refused(self, tmp_path: Path) -> None:
        wider = {**GRANTED, "scopes": [SEND_SCOPE, READ_SCOPE]}
        with pytest.raises(TokenError, match="granted more than this agent asked for"):
            authorize(client_file(tmp_path), tmp_path / "t.json", returning(wider))
    def test_a_grant_with_no_refresh_token_is_refused(self, tmp_path: Path) -> None:
        without = {k: v for k, v in GRANTED.items() if k != "refresh_token"}
        with pytest.raises(TokenError, match="no refresh token"):
            authorize(client_file(tmp_path), tmp_path / "t.json", returning(without))
    def test_the_refresh_less_message_says_to_revoke(self, tmp_path: Path) -> None:
        without = {**GRANTED, "refresh_token": ""}
        with pytest.raises(TokenError, match="myaccount.google.com/permissions"):
            authorize(client_file(tmp_path), tmp_path / "t.json", returning(without))
    def test_a_flow_returning_something_that_is_not_a_credential(self, tmp_path: Path) -> None:
        with pytest.raises(TokenError, match="not a credential"):
            authorize(client_file(tmp_path), tmp_path / "t.json", returning("ok"))
    @pytest.mark.parametrize(
        "body",
        [
            {**GRANTED, "scopes": [SEND_SCOPE, READ_SCOPE]},
            {**GRANTED, "refresh_token": ""},
            "not a credential",
        ],
    )
    def test_nothing_is_written_when_the_grant_is_refused(
        self, tmp_path: Path, body: object
    ) -> None:
        destination = tmp_path / "t.json"
        with pytest.raises(TokenError):
            authorize(client_file(tmp_path), destination, returning(body))
        assert not destination.exists()
