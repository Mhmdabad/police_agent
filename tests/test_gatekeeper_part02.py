from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_gatekeeper")).items() if not k.startswith("__")})

class TestTheOrderIsCheapestAndMostFinalFirst:
    def test_a_locked_pipeline_is_refused_before_the_quota_is_touched(self, tmp_path: Path) -> None:
        (tmp_path / ".locked_cop.json").write_text(json.dumps({"reason": "earlier"}))
        gate = gatekeeper(tmp_path)
        with pytest.raises(Rejected, match="DOS detector"):
            gate.admit()
        assert gate.quota.used() == 0
        assert gate.limiter.bucket.tokens() == 2.0
    def test_an_exhausted_quota_is_refused_before_a_token_is_spent(self, tmp_path: Path) -> None:
        gate = gatekeeper(tmp_path, limit=1)
        gate.admit()
        tokens = gate.limiter.bucket.tokens()
        with pytest.raises(Rejected, match="quota"):
            gate.admit()
        assert gate.limiter.bucket.tokens() == tokens
    def test_each_refusal_names_its_gate(self, tmp_path: Path) -> None:
        (tmp_path / ".locked_cop.json").write_text(json.dumps({"reason": "x"}))
        with pytest.raises(Rejected, match="^DOS detector:"):
            gatekeeper(tmp_path).admit()
