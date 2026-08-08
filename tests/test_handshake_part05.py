from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_handshake")).items() if not k.startswith("__")})

class TestRecordingTheDeclaration:
    def book(self) -> AddressBook:
        return AddressBook.of(greet("police", PUBLIC_COP), greet("thief", PUBLIC_THIEF))
    def test_it_writes_the_named_file(self, tmp_path: Path) -> None:
        path = record(tmp_path, "uoh26-s82kma9e", self.book())
        assert path.name == "declaration_uoh26-s82kma9e.json"
        assert json.loads(path.read_text())[ADDRESS_KEY]["thief"]["public_url"] == (
            f"{PUBLIC_THIEF}/mcp"
        )
    def test_it_creates_the_directory(self, tmp_path: Path) -> None:
        assert record(tmp_path / "artefacts", "g1", self.book()).exists()
    def test_it_merges_rather_than_overwrites(self, tmp_path: Path) -> None:
        path = tmp_path / "declaration_g1.json"
        path.write_text(json.dumps({"hardware": {"cpu": "M2"}, "token_ceiling": 200000}))
        merged: dict[str, Any] = json.loads(record(tmp_path, "g1", self.book()).read_text())
        assert merged["hardware"] == {"cpu": "M2"}
        assert merged["token_ceiling"] == 200000
        assert ADDRESS_KEY in merged
    def test_re_recording_replaces_only_the_addresses(self, tmp_path: Path) -> None:
        record(tmp_path, "g1", self.book())
        second = AddressBook.of(greet("police", LOCAL_COP), greet("thief", LOCAL_THIEF))
        merged = json.loads(record(tmp_path, "g1", second).read_text())
        assert merged[ADDRESS_KEY]["police"]["public_url"] == f"{LOCAL_COP}/mcp"
    def test_it_refuses_a_one_sided_record(self, tmp_path: Path) -> None:
        with pytest.raises(HandshakeError, match="proves nothing at audit"):
            record(tmp_path, "g1", AddressBook({"police": {}}))
    def test_it_refuses_a_declaration_that_is_not_an_object(self, tmp_path: Path) -> None:
        (tmp_path / "declaration_g1.json").write_text("[1, 2, 3]")
        with pytest.raises(Exception, match="declaration"):
            record(tmp_path, "g1", self.book())
    def test_it_refuses_a_game_id_that_would_escape_the_directory(self, tmp_path: Path) -> None:
        with pytest.raises(Exception, match="filename component"):
            record(tmp_path, "../../etc/passwd", self.book())
