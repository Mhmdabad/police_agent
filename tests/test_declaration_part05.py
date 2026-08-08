from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_declaration")).items() if not k.startswith("__")})

class TestTheFile:
    def test_the_name_derives_from_the_game_id(self) -> None:
        assert declared().filename == "declaration_uoh26-s82kma9e.json"
    def test_it_writes_and_reads_back(self, tmp_path: Path) -> None:
        path = declared().write(tmp_path)
        assert json.loads(path.read_text())["game_uid"] == "u-0001"
    def test_it_creates_the_directory(self, tmp_path: Path) -> None:
        assert declared().write(tmp_path / "artefacts" / "deep").exists()
    def test_the_bytes_are_stable(self, tmp_path: Path) -> None:
        first = declared().write(tmp_path / "a").read_text()
        second = declared().write(tmp_path / "b").read_text()
        assert first == second
        assert first.endswith("}\n")
    def test_the_written_file_carries_the_signature(self, tmp_path: Path) -> None:
        body = json.loads(declared().write(tmp_path).read_text())
        assert body["signature"] == declared().signature
