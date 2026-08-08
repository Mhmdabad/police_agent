from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_quota")).items() if not k.startswith("__")})

class TestStatusIsSafeToPrint:
    def test_it_reads_as_a_sentence(self, tmp_path: Path) -> None:
        gate = quota(tmp_path)
        gate.reserve()
        assert gate.status() == "1/3 sends used on 2026-08-05 UTC"
    def test_it_does_not_raise_on_a_damaged_ledger(self, tmp_path: Path) -> None:
        (tmp_path / ".quota_cop.json").write_text("{half a wr")
        assert "blocked" in quota(tmp_path).status()
