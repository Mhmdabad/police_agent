from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_gatekeeper")).items() if not k.startswith("__")})

class TestAllThreeGatesRun:
    def test_a_clean_request_is_admitted(self, tmp_path: Path) -> None:
        assert gatekeeper(tmp_path).admit() is None
    def test_admission_spends_a_quota_slot(self, tmp_path: Path) -> None:
        gate = gatekeeper(tmp_path)
        gate.admit()
        assert gate.quota.used() == 1
    def test_admission_spends_a_token(self, tmp_path: Path) -> None:
        gate = gatekeeper(tmp_path)
        gate.admit()
        assert gate.limiter.bucket.tokens() == 1.0
