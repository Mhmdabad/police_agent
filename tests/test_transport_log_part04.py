from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_transport_log")).items() if not k.startswith("__")})

class TestWritingIt:
    def test_it_writes_the_rendered_log(self, tmp_path: Path) -> None:
        log = TransportLog(clock=Ticking())
        log.record(UNREACHABLE, "receive_turn", URL, "peer gone")
        path = log.write(tmp_path / "transport_g1_g01.log")
        assert "peer gone" in path.read_text()
    def test_it_creates_the_directory(self, tmp_path: Path) -> None:
        assert TransportLog().write(tmp_path / "artefacts" / "t.log").exists()
    def test_it_replaces_rather_than_appends(self, tmp_path: Path) -> None:
        path = tmp_path / "t.log"
        path.write_text("a previous match\n")
        TransportLog().write(path)
        assert "a previous match" not in path.read_text()
    def test_the_filename_names_the_sub_game(self) -> None:
        assert transport_log_filename("uoh26-s82kma9e", 3) == "transport_uoh26-s82kma9e_g03.log"
    def test_the_filename_refuses_a_game_id_that_would_escape(self) -> None:
        with pytest.raises(NamingError):
            transport_log_filename("../etc/passwd", 1)
