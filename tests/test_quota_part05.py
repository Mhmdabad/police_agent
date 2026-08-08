from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_quota")).items() if not k.startswith("__")})

class TestAnUnreadableLedgerFailsClosed:
    def test_a_damaged_file_refuses_rather_than_assuming_zero(self, tmp_path: Path) -> None:
        path = tmp_path / ".quota_cop.json"
        path.write_text("{half a wr")
        with pytest.raises(QuotaError, match="cannot be read"):
            quota(tmp_path).used()
    def test_a_file_that_is_not_a_count_refuses(self, tmp_path: Path) -> None:
        path = tmp_path / ".quota_cop.json"
        path.write_text(json.dumps({"day": "2026-08-05", "used": "lots"}))
        with pytest.raises(QuotaError, match="not a count"):
            quota(tmp_path).used()
    def test_a_json_list_refuses(self, tmp_path: Path) -> None:
        path = tmp_path / ".quota_cop.json"
        path.write_text("[]")
        with pytest.raises(QuotaError, match="not a count"):
            quota(tmp_path).used()
    def test_a_directory_in_place_of_the_ledger_refuses(self, tmp_path: Path) -> None:
        (tmp_path / ".quota_cop.json").mkdir()
        with pytest.raises(QuotaError, match="cannot be read"):
            quota(tmp_path).used()
    def test_reserving_against_a_damaged_ledger_refuses_too(self, tmp_path: Path) -> None:
        (tmp_path / ".quota_cop.json").write_text("{half a wr")
        with pytest.raises(QuotaError):
            quota(tmp_path).reserve()
    def test_the_message_names_the_deliberate_remedy(self, tmp_path: Path) -> None:
        (tmp_path / ".quota_cop.json").write_text("{half a wr")
        with pytest.raises(QuotaError, match="clear it deliberately"):
            quota(tmp_path).used()
    def test_reset_clears_it_and_is_the_only_thing_that_does(self, tmp_path: Path) -> None:
        gate = quota(tmp_path)
        (tmp_path / ".quota_cop.json").write_text("{half a wr")
        gate.reset()
        assert gate.used() == 0
