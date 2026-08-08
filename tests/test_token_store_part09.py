from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_store")).items() if not k.startswith("__")})

class TestRefreshing:
    @staticmethod
    def client() -> dict[str, Any]:
        return {
            "client_id": CLIENT,
            "client_secret": "GOCSPX-not-real",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    @staticmethod
    def returning(body: object) -> Exchange:
        def exchange(refresh_token: str, client: dict[str, Any]) -> dict[str, Any]:
            return cast("dict[str, Any]", body)
        return exchange
    def test_it_writes_the_new_credential_back(self, tmp_path: Path) -> None:
        path = stored(tmp_path)
        token = read(path, CLIENT)
        fresh = {**GOOD, "token": "ya29.brand-new", "expiry": "2099-06-01T00:00:00Z"}
        refreshed = refresh(path, token, self.client(), self.returning(fresh))
        assert refreshed.expiry is not None
        assert json.loads(path.read_text())["token"] == "ya29.brand-new"
    def test_the_next_process_starts_from_the_new_one(self, tmp_path: Path) -> None:
        path = stored(tmp_path)
        fresh = {**GOOD, "token": "ya29.brand-new"}
        refresh(path, read(path, CLIENT), self.client(), self.returning(fresh))
        assert read(path, CLIENT).refresh_token == GOOD["refresh_token"]
    def test_it_keeps_the_refresh_token_when_the_response_omits_it(self, tmp_path: Path) -> None:
        path = stored(tmp_path)
        without = {k: v for k, v in GOOD.items() if k != "refresh_token"}
        refresh(path, read(path, CLIENT), self.client(), self.returning(without))
        assert read(path, CLIENT).refresh_token == GOOD["refresh_token"]
    def test_it_keeps_the_role(self, tmp_path: Path) -> None:
        path = stored(tmp_path, declared_role="police")
        token = read(path, CLIENT, role="police")
        refresh(path, token, self.client(), self.returning(dict(GOOD)))
        assert read(path, CLIENT, role="police").role == "police"
    def test_an_over_scoped_refresh_is_refused(self, tmp_path: Path) -> None:
        path = stored(tmp_path)
        wider = {**GOOD, "scopes": [SEND_SCOPE, READ_SCOPE]}
        with pytest.raises(TokenError, match="not one we may hold"):
            refresh(path, read(path, CLIENT), self.client(), self.returning(wider))
    def test_a_refresh_that_returns_nothing_usable_is_refused(self, tmp_path: Path) -> None:
        path = stored(tmp_path)
        with pytest.raises(TokenError, match="not a credential"):
            refresh(path, read(path, CLIENT), self.client(), self.returning("ok"))
    def test_a_refresh_with_no_refresh_token_anywhere_is_refused(self, tmp_path: Path) -> None:
        path = stored(tmp_path)
        token = read(path, CLIENT)
        empty = {**GOOD, "refresh_token": ""}
        stripped = StoredToken(client_id=token.client_id, refresh_token="", scopes=token.scopes)
        with pytest.raises(TokenError, match="nothing to use"):
            refresh(path, stripped, self.client(), self.returning(empty))
    def test_a_bad_refresh_leaves_the_existing_credential_alone(self, tmp_path: Path) -> None:
        path = stored(tmp_path)
        before = path.read_text()
        wider = {**GOOD, "scopes": [SEND_SCOPE, READ_SCOPE]}
        with pytest.raises(TokenError):
            refresh(path, read(path, CLIENT), self.client(), self.returning(wider))
        assert path.read_text() == before
    def test_the_refreshed_file_is_still_owner_only(self, tmp_path: Path) -> None:
        path = stored(tmp_path)
        refresh(path, read(path, CLIENT), self.client(), self.returning(dict(GOOD)))
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
