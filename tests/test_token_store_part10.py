from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_store")).items() if not k.startswith("__")})

class TestTheRealRefreshIsWiredCorrectly:
    def test_it_passes_the_client_and_asks_for_our_scope_only(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen: dict[str, Any] = {}
        class FakeCredentials:
            def __init__(self, **kwargs: object) -> None:
                seen.update(kwargs)
            def refresh(self, request: object) -> None:
                seen["refreshed_with"] = type(request).__name__
            @staticmethod
            def to_json() -> str:
                return json.dumps(GOOD)
        class FakeRequest:
            pass
        credentials_module = pytest.importorskip("google.oauth2.credentials")
        requests_module = pytest.importorskip("google.auth.transport.requests")
        monkeypatch.setattr(credentials_module, "Credentials", FakeCredentials)
        monkeypatch.setattr(requests_module, "Request", FakeRequest)
        client = {
            "client_id": CLIENT,
            "client_secret": "GOCSPX-not-real",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        body = google_refresh("1//refresh-not-real", client)
        assert body == GOOD
        assert seen["refresh_token"] == "1//refresh-not-real"
        assert seen["client_id"] == CLIENT
        assert seen["token_uri"] == "https://oauth2.googleapis.com/token"
        assert seen["scopes"] == [SEND_SCOPE], "a refresh must not widen the grant"
        assert seen["token"] is None, "no stale access token is carried in"
        assert seen["refreshed_with"] == "FakeRequest"
