from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_authorize")).items() if not k.startswith("__")})

class TestTheHappyPath:
    def test_it_writes_a_token_the_store_will_accept(self, tmp_path: Path) -> None:
        written = authorize(client_file(tmp_path), tmp_path / "t.json", returning(GRANTED))
        assert read(written, CLIENT).refresh_token == GRANTED["refresh_token"]
    def test_the_written_file_is_owner_only(self, tmp_path: Path) -> None:
        written = authorize(client_file(tmp_path), tmp_path / "t.json", returning(GRANTED))
        assert stat.S_IMODE(written.stat().st_mode) == 0o600
    def test_it_asks_only_for_the_send_scope(self, tmp_path: Path) -> None:
        seen: list[Any] = []
        authorize(client_file(tmp_path), tmp_path / "t.json", returning(GRANTED, seen))
        assert seen[0][1] == (SEND_SCOPE,)
    def test_it_hands_the_flow_the_installed_section(self, tmp_path: Path) -> None:
        seen: list[Any] = []
        authorize(client_file(tmp_path), tmp_path / "t.json", returning(GRANTED, seen))
        assert seen[0][0] == DESKTOP["installed"]
