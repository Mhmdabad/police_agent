from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_config_agreement")).items() if not k.startswith("__")})

class TestWhatWeSendCarriesTheBinding:
    def test_the_outbound_message_names_the_series(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        with pytest.raises(MatchAborted):
            ours.orchestrator.agree_config(parameters(), game_uid=GAME_UID, timeout=BRIEF)
        assert theirs.inboxes.digests.get_nowait() == {
            "config_sha256": agreed_digest(),
            "game_uid": GAME_UID,
        }
    def test_the_runner_binds_the_digest_to_its_own_declaration(
        self, wire: tuple[Side, Side], tmp_path: Path
    ) -> None:
        ours, theirs = fresh(wire)
        runner = a_runner(ours, parameters(), tmp_path)
        with pytest.raises(MatchAborted):
            runner.agree(timeout=BRIEF)
        assert theirs.inboxes.digests.get_nowait()["game_uid"] == runner.declaration.game_uid
