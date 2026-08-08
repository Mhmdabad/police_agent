from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_store")).items() if not k.startswith("__")})

class TestSaving:
    def test_it_round_trips_through_read(self, tmp_path: Path) -> None:
        path = save(tmp_path / "token_cop.json", GOOD)
        assert read(path, CLIENT).refresh_token == GOOD["refresh_token"]
    def test_the_file_is_readable_only_by_its_owner(self, tmp_path: Path) -> None:
        path = save(tmp_path / "token_cop.json", GOOD)
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    def test_an_existing_world_readable_file_is_narrowed(self, tmp_path: Path) -> None:
        path = tmp_path / "token_cop.json"
        path.write_text("{}")
        path.chmod(0o644)
        save(path, GOOD)
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    def test_it_creates_the_directory(self, tmp_path: Path) -> None:
        path = save(tmp_path / "nested" / "deeper" / "token_cop.json", GOOD)
        assert path.exists()
    def test_it_truncates_rather_than_appending(self, tmp_path: Path) -> None:
        path = tmp_path / "token_cop.json"
        path.write_text(json.dumps({**GOOD, "refresh_token": "old"}) + "\n" * 200)
        save(path, GOOD)
        assert json.loads(path.read_text())["refresh_token"] == GOOD["refresh_token"]
