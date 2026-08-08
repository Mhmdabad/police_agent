from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_crypto")).items() if not k.startswith("__")})

class TestAudit:
    def _record(self, payload: dict[str, object]) -> dict[str, object]:
        return {"payload": payload, **seal(payload)}
    def test_an_honest_match_passes(self) -> None:
        audit([self._record({"step": n, "move": "N"}) for n in range(35)])
    def test_a_single_tampered_step_is_caught(self) -> None:
        records = [self._record({"step": n, "move": "N"}) for n in range(5)]
        records[3]["payload"] = {"step": 3, "move": "S"}
        with pytest.raises(CryptoError, match="tampering at step 3"):
            audit(records)
    def test_the_failing_step_is_named(self) -> None:
        records = [self._record({"step": n, "move": "N"}) for n in range(10)]
        records[7]["payload"] = {"step": 7, "move": "W"}
        with pytest.raises(CryptoError, match="step 7"):
            audit(records)
    def test_a_malformed_record_is_reported_not_crashed(self) -> None:
        with pytest.raises(CryptoError, match="missing 'nonce'"):
            audit([{"payload": {"step": 0}, "commit": "x"}])
    def test_an_empty_audit_passes(self) -> None:
        audit([])
