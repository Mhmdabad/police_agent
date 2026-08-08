from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_localhost_match")).items() if not k.startswith("__")})

class TestTheMatchProducesItsOwnEvidence:
    @staticmethod
    def artefacts_for(side: Side) -> ArtefactSet:
        uid, game_id = played_log(side).game_uid, played_log(side).game_id
        return ArtefactSet(
            declaration=build_declaration(side.role, game_id, uid),
            configs=(
                lock(
                    game_id=game_id,
                    game_uid=uid,
                    sub_game=1,
                    parameters=parameters(),
                    agreed_between=("uoh26-cops", "uoh26-others"),
                ),
            ),
            logs=(played_log(side),),
            result=result_for(side, game_id, uid),
        )
    def test_the_set_is_coherent(self, played: tuple[Side, Side, Path]) -> None:
        cop, _, _ = played
        coherence = self.artefacts_for(cop).check()
        assert coherence.coherent, str(coherence)
    def test_all_four_kinds_are_written(self, played: tuple[Side, Side, Path]) -> None:
        cop, _, where = played
        written = self.artefacts_for(cop).write(where / "cop-artefacts")
        assert {path.name for path in written} == {
            "declaration_uoh26-s82kma9e.json",
            "config_uoh26-s82kma9e_g01.json",
            "log_uoh26-s82kma9e_g01.json",
            "result_uoh26-s82kma9e.json",
        }
    def test_the_written_log_still_stamps_verified_ok(
        self, played: tuple[Side, Side, Path]
    ) -> None:
        cop, _, where = played
        written = self.artefacts_for(cop).write(where / "cop-set")
        log = next(path for path in written if path.name.startswith("log_"))
        assert walk(load(log)).stamp is Stamp.VERIFIED_OK
    def test_the_result_records_the_commit_the_game_was_played_at(
        self, played: tuple[Side, Side, Path]
    ) -> None:
        cop, _, where = played
        written = self.artefacts_for(cop).write(where / "cop-commit")
        result = next(path for path in written if path.name.startswith("result_"))
        body = json.loads(result.read_text())
        assert body["sub_games"][0]["commit_hash"]
        assert len(body["repositories"]) == 4
    def test_both_sides_produce_sets_that_agree_on_the_match(
        self, played: tuple[Side, Side, Path]
    ) -> None:
        cop, thief, _ = played
        ours, theirs = self.artefacts_for(cop), self.artefacts_for(thief)
        assert ours.game_uid == theirs.game_uid
        assert ours.game_id == theirs.game_id
        assert ours.check().coherent and theirs.check().coherent
