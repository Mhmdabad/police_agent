from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_match_log")).items() if not k.startswith("__")})

class TestTheFile:
    def test_it_is_named_for_the_game_and_sub_game(self, tmp_path: Path) -> None:
        assert played().write(tmp_path).name == "log_uoh26-s82kma9e_g03.json"
    def test_it_writes_and_creates_the_directory(self, tmp_path: Path) -> None:
        path = played(2).write(tmp_path / "artefacts")
        written = json.loads(path.read_text())
        assert [row["step"] for row in written["steps"]] == [1, 2]
        assert written["role"] == "police"
    def test_steps_are_sorted_so_identical_histories_agree(self, tmp_path: Path) -> None:
        forwards, backwards = log(), log()
        for step in (1, 2, 3):
            forwards.commit(step, DIGEST)
        for step in (3, 2, 1):
            backwards.commit(step, DIGEST)
        assert forwards.to_dict() == backwards.to_dict()
    def test_a_game_id_that_would_escape_the_directory_is_refused(self) -> None:
        with pytest.raises(NamingError):
            MatchLog(game_id="../../etc/passwd", sub_game=1, role="police")
    def test_a_sub_game_outside_the_series_is_refused(self) -> None:
        with pytest.raises(NamingError):
            MatchLog(game_id="g1", sub_game=0, role="police")
    def test_a_role_the_wire_does_not_name_is_refused(self) -> None:
        with pytest.raises(MatchLogError, match="role must be one of"):
            MatchLog(game_id="g1", sub_game=1, role="cop")
