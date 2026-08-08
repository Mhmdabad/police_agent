from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_authorize")).items() if not k.startswith("__")})

class TestTheRealFlowIsWiredCorrectly:
    def test_it_wraps_the_client_in_installed_and_passes_the_scopes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen: dict[str, Any] = {}
        class FakeCredentials:
            @staticmethod
            def to_json() -> str:
                return json.dumps(GRANTED)
        class FakeFlow:
            @staticmethod
            def from_client_config(config: dict[str, Any], scopes: list[str]) -> "FakeFlow":
                seen["config"], seen["scopes"] = config, scopes
                return FakeFlow()
            @staticmethod
            def run_local_server(port: int) -> FakeCredentials:
                seen["port"] = port
                return FakeCredentials()
        module = pytest.importorskip("google_auth_oauthlib.flow")
        monkeypatch.setattr(module, "InstalledAppFlow", FakeFlow)
        body = google_flow(DESKTOP["installed"], [SEND_SCOPE])
        assert body == GRANTED
        assert seen["config"] == {"installed": DESKTOP["installed"]}
        assert seen["scopes"] == [SEND_SCOPE]
        assert seen["port"] == 0, "an ephemeral port, so two agents can authorize at once"
