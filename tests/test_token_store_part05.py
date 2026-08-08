from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_store")).items() if not k.startswith("__")})

class TestItRefusesWhatItCannotRead:
    def test_a_missing_file_is_a_token_error(self, tmp_path: Path) -> None:
        with pytest.raises(TokenError, match="no token_cop.json"):
            read(tmp_path / "token_cop.json", CLIENT)
    def test_a_directory_is_a_token_error_not_a_crash(self, tmp_path: Path) -> None:
        (tmp_path / "token_cop.json").mkdir()
        with pytest.raises(TokenError, match="cannot read"):
            read(tmp_path / "token_cop.json", CLIENT)
    def test_a_non_json_file_is_a_token_error(self, tmp_path: Path) -> None:
        path = tmp_path / "token_cop.json"
        path.write_text("half a fi")
        with pytest.raises(TokenError, match="is not JSON"):
            read(path, CLIENT)
    def test_a_json_list_is_a_token_error(self, tmp_path: Path) -> None:
        path = tmp_path / "token_cop.json"
        path.write_text("[]")
        with pytest.raises(TokenError, match="not a token object"):
            read(path, CLIENT)
    def test_a_missing_scope_field_is_a_token_error(self, tmp_path: Path) -> None:
        body = {k: v for k, v in GOOD.items() if k != "scopes"}
        path = tmp_path / "token_cop.json"
        path.write_text(json.dumps(body))
        with pytest.raises(TokenError, match="expected a list of scope strings"):
            read(path, CLIENT)
    def test_a_space_separated_scope_field_is_accepted(self, tmp_path: Path) -> None:
        body = {k: v for k, v in GOOD.items() if k != "scopes"} | {"scope": SEND_SCOPE}
        path = tmp_path / "token_cop.json"
        path.write_text(json.dumps(body))
        assert read(path, CLIENT).scopes == (SEND_SCOPE,)
