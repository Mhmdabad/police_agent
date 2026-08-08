from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_store")).items() if not k.startswith("__")})

class TestTheThreeRefusals:
    def test_an_over_scoped_token_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(TokenError, match="will not hold"):
            read(stored(tmp_path, scopes=[SEND_SCOPE, READ_SCOPE]), CLIENT)
    def test_a_token_with_no_refresh_token_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(TokenError, match="stops working within the hour"):
            read(stored(tmp_path, refresh_token=""), CLIENT)
    def test_the_refresh_less_message_explains_why_it_happened(self, tmp_path: Path) -> None:
        body = {k: v for k, v in GOOD.items() if k != "refresh_token"}
        path = tmp_path / "token_cop.json"
        path.write_text(json.dumps(body))
        with pytest.raises(TokenError, match="authorised before"):
            read(path, CLIENT)
    def test_a_token_from_another_client_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(TokenError, match="different client"):
            read(stored(tmp_path, client_id=OTHER), CLIENT)
    def test_the_foreign_client_message_names_the_likely_cause(self, tmp_path: Path) -> None:
        with pytest.raises(TokenError, match="copied between the two"):
            read(stored(tmp_path, client_id=OTHER), CLIENT)
