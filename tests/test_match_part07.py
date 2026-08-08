from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_match")).items() if not k.startswith("__")})

class TestWritingTheEvidence:
    def test_it_writes_one_config_and_one_log_per_sub_game(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path)
        runner.outcomes.extend([an_outcome(1), an_outcome(2)])
        written = runner.write(result_for_two())
        assert len([p for p in written if p.name.startswith("config_")]) == 2
        assert len([p for p in written if p.name.startswith("log_")]) == 2
    def test_an_incoherent_set_is_refused(self, tmp_path: Path) -> None:
        from cop_agent.infra.artefacts import ArtefactError
        runner = a_runner(tmp_path)
        runner.outcomes.append(an_outcome(1))
        with pytest.raises(ArtefactError):
            runner.write(result_for_two())
    def test_every_file_carries_the_uid(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path)
        runner.outcomes.extend([an_outcome(1), an_outcome(2)])
        for path in runner.write(result_for_two()):
            assert json.loads(path.read_text())["game_uid"] == "u-0001"
