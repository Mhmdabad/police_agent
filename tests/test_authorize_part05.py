from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_authorize")).items() if not k.startswith("__")})

class TestTheRunnerIsResolvedAtCallTimeNotImportTime:
    def test_substituting_the_module_attribute_takes_effect(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen: list[Any] = []
        monkeypatch.setattr("cop_agent.infra.authorize.google_flow", returning(GRANTED, seen))
        authorize(client_file(tmp_path), tmp_path / "t.json")
        assert seen, "the default was captured at import time and the real flow ran"
    def test_an_explicit_runner_still_wins(self, tmp_path: Path) -> None:
        seen: list[Any] = []
        authorize(client_file(tmp_path), tmp_path / "t.json", returning(GRANTED, seen))
        assert len(seen) == 1
