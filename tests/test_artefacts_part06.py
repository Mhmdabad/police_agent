from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_artefacts")).items() if not k.startswith("__")})

class TestWriting:
    def test_a_coherent_set_writes_all_four_kinds(self, tmp_path: Path) -> None:
        written = a_set().write(tmp_path)
        assert len(written) == 6
        assert {path.name for path in written} == set(a_set().filenames())
    def test_every_written_file_is_readable_json(self, tmp_path: Path) -> None:
        for path in a_set().write(tmp_path):
            assert json.loads(path.read_text())
    def test_every_written_file_carries_the_uid(self, tmp_path: Path) -> None:
        for path in a_set().write(tmp_path):
            assert json.loads(path.read_text())["game_uid"] == UID
    def test_an_incoherent_set_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(ArtefactError, match="incoherent artefact set"):
            a_set(result=a_result(uid="u-9999")).write(tmp_path)
    def test_nothing_is_written_when_it_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(ArtefactError):
            a_set(result=a_result(uid="u-9999")).write(tmp_path)
        assert list(tmp_path.iterdir()) == []
    def test_the_refusal_names_what_disagreed(self, tmp_path: Path) -> None:
        with pytest.raises(ArtefactError, match="different game_uid"):
            a_set(result=a_result(uid="u-9999")).write(tmp_path)
