from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_match")).items() if not k.startswith("__")})

class TestTheDoorIsOpenedBeforeAnythingInvitesAMessage:
    def watched(self, tmp_path: Path) -> tuple[MatchRunner, "Watching"]:
        transport = Watching()
        runner = a_runner(tmp_path, transport=transport)  # type: ignore[arg-type]
        transport.inboxes = runner.orchestrator.inboxes
        return runner, transport
    def test_the_series_is_bound_before_its_first_agreement_crosses_the_wire(
        self, tmp_path: Path
    ) -> None:
        runner, transport = self.watched(tmp_path)
        with pytest.raises(MatchAborted):
            runner.agree(timeout=0.01)
        assert transport.bound[0] == ("u-0001", 1)
    def test_a_boundary_is_bound_before_it_is_announced(self, tmp_path: Path) -> None:
        runner, transport = self.watched(tmp_path)
        with pytest.raises(MatchAborted):
            runner.rehandshake(4, timeout=0.01)
        assert transport.bound[0] == ("u-0001", 4)
