from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_subgame")).items() if not k.startswith("__")})

class TestTheLogItProduces:
    def test_the_replay_app_stamps_it_verified_ok(self, tmp_path: Path) -> None:
        game, _, log = a_subgame(tmp_path, max_steps=4)
        game.play()
        result = walk(load(log.write(tmp_path)))
        assert result.stamp is Stamp.VERIFIED_OK, str(result)
        assert result.verified == 4
    def test_every_step_has_all_three_slots(self, tmp_path: Path) -> None:
        game, _, log = a_subgame(tmp_path, max_steps=3)
        game.play()
        for entry in log.entries.values():
            assert entry.commit and entry.reveal and entry.nonce
    def test_a_third_party_could_fully_re_verify_it(self, tmp_path: Path) -> None:
        game, _, log = a_subgame(tmp_path, max_steps=3)
        game.play()
        assert log.verifiable().complete, str(log.verifiable())
    def test_the_log_records_our_sealed_record_not_the_wire_message(self, tmp_path: Path) -> None:
        game, _, log = a_subgame(tmp_path, max_steps=1)
        game.play()
        reveal = log.entries[1].reveal
        assert reveal is not None
        assert "state" in reveal and "timestamp" not in reveal
    def test_no_nonce_is_written_before_the_sub_game_ends(self, tmp_path: Path) -> None:
        game, _, log = a_subgame(tmp_path, max_steps=3)
        game._one_step(1)  # noqa: SLF001 - the point is the state mid-match
        assert log.unopened() == [1]
