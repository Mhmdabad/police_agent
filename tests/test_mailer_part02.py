from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mailer")).items() if not k.startswith("__")})

class TestTheGatesAreInFrontOfIt:
    def test_a_quota_slot_is_spent(self, tmp_path: Path) -> None:
        mailer, _, gate = a_mailer(tmp_path)
        mailer.send_report(a_report(), "cop@example.com")
        assert gate.quota.used() == 1
    def test_the_attempt_reaches_the_dos_detector(self, tmp_path: Path) -> None:
        mailer, _, gate = a_mailer(tmp_path)
        mailer.send_report(a_report(), "cop@example.com")
        assert len(gate.detector.recent) == 1
    def test_an_exhausted_quota_stops_it_before_the_api(self, tmp_path: Path) -> None:
        mailer, api, _ = a_mailer(tmp_path, limit=1)
        mailer.send_report(a_report(), "cop@example.com")
        with pytest.raises(SendError, match="quota"):
            mailer.send_report(a_report(), "cop@example.com")
        assert len(api.calls) == 1, "a refused report still reached the API"
    def test_a_locked_pipeline_stops_it_before_the_api(self, tmp_path: Path) -> None:
        mailer, api, gate = a_mailer(tmp_path)
        (tmp_path / ".locked_cop.json").write_text(json.dumps({"reason": "earlier storm"}))
        with pytest.raises(SendError, match="DOS detector"):
            mailer.send_report(a_report(), "cop@example.com")
        assert api.calls == []
    def test_the_refusal_says_the_report_was_not_sent(self, tmp_path: Path) -> None:
        mailer, _, _ = a_mailer(tmp_path)
        (tmp_path / ".locked_cop.json").write_text(json.dumps({"reason": "x"}))
        with pytest.raises(SendError, match="the report was not sent"):
            mailer.send_report(a_report(), "cop@example.com")
    def test_an_empty_bucket_waits_rather_than_refusing(self, tmp_path: Path) -> None:
        mailer, api, gate = a_mailer(tmp_path, capacity=2.0)
        for _ in range(3):
            mailer.send_report(a_report(), "cop@example.com")
        assert len(api.calls) == 3
        assert mailer.waits, "the third send should have waited for a token"
