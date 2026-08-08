from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_match_log")).items() if not k.startswith("__")})

class TestWhetherAThirdPartyCanReVerify:
    def test_a_finished_log_can_be(self) -> None:
        result = sealed_log().verifiable()
        assert result.complete
        assert "fully re-verify" in str(result)
    def test_a_log_with_no_config_hash_cannot(self) -> None:
        log = sealed_log()
        log.config_sha256 = ""
        assert not log.verifiable().complete
        assert "which physics applied" in str(log.verifiable())
    def test_a_log_with_no_game_uid_cannot(self) -> None:
        log = sealed_log()
        log.game_uid = ""
        assert "ties this log to the declaration" in str(log.verifiable())
    def test_a_log_with_no_steps_cannot(self) -> None:
        assert "a log of nothing verifies nothing" in str(sealed_log(steps=0).verifiable())
    def test_a_mid_match_log_cannot_yet(self) -> None:
        result = sealed_log(disclose=False).verifiable()
        assert not result.complete
        assert "nonces for steps [1, 2]" in str(result)
    def test_a_step_with_no_reveal_is_named(self) -> None:
        log = sealed_log()
        log.entries[2].reveal = None
        assert "reveals for steps [2]" in str(log.verifiable())
    def test_it_names_everything_missing_at_once(self) -> None:
        log = MatchLog(game_id="uoh26-s82kma9e", sub_game=1, role="police")
        assert len(log.verifiable().missing) == 3
    def test_the_header_reaches_the_file(self, tmp_path: Path) -> None:
        body = json.loads(sealed_log().write(tmp_path).read_text())
        assert body["game_uid"] == "u-0001"
        assert body["config_sha256"] == "c" * 64
