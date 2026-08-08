from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_orchestrator")).items() if not k.startswith("__")})

class TestConfigAgreement:
    def test_advertises_the_digest_of_the_loaded_config(self) -> None:
        config = shipped()
        orch, transport = orchestrator({"ok": True})
        answered(orch, config_sha256(config))
        assert orch.agree_config(config) == config_sha256(config)
        assert transport.calls[0]["payload"]["message"]["config_sha256"] == config_sha256(config)
    def test_it_negotiates_over_the_wire_tool(self) -> None:
        orch, transport = orchestrator({"ok": True})
        answered(orch, config_sha256(shipped()))
        orch.agree_config(shipped())
        assert transport.calls[0]["tool"] == "negotiate"
    def test_a_mismatch_aborts_rather_than_playing_on(self) -> None:
        orch, _ = orchestrator({"ok": False, "detail": "digest mismatch"})
        with pytest.raises(MatchAborted) as excinfo:
            orch.agree_config(shipped())
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
        assert "digest mismatch" in excinfo.value.detail
    def test_a_changed_config_changes_the_advertised_digest(self) -> None:
        config = shipped()
        orch, _ = orchestrator({"ok": True}, {"ok": True})
        answered(orch, config_sha256(config))
        first = orch.agree_config(config)
        config["world"]["map_area"] = "London"
        answered(orch, config_sha256(config))
        assert orch.agree_config(config) != first
    def test_their_ok_is_not_their_agreement(self) -> None:
        config = shipped()
        orch, _ = orchestrator({"ok": True})
        answered(orch, config_sha256({**config, "world": {"map_area": "London"}}))
        with pytest.raises(MatchAborted) as excinfo:
            orch.agree_config(config)
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
    def test_the_accusation_carries_both_digests(self) -> None:
        config = shipped()
        theirs = config_sha256({**config, "world": {"map_area": "London"}})
        orch, _ = orchestrator({"ok": True})
        answered(orch, theirs)
        with pytest.raises(MatchAborted) as excinfo:
            orch.agree_config(config)
        assert theirs in excinfo.value.detail
        assert config_sha256(config) in excinfo.value.detail
    def test_silence_after_an_ok_is_a_timeout(self) -> None:
        orch, _ = orchestrator({"ok": True})
        with pytest.raises(MatchAborted) as excinfo:
            orch.agree_config(shipped(), timeout=0.0)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
    def test_the_series_is_named_in_what_we_send(self) -> None:
        orch, transport = orchestrator({"ok": True})
        answered(orch, config_sha256(shipped()), game_uid="u-0001")
        orch.agree_config(shipped(), game_uid="u-0001")
        assert transport.calls[0]["payload"]["message"]["game_uid"] == "u-0001"
    def test_an_agreement_about_another_series_does_not_open_this_one(self) -> None:
        orch, _ = orchestrator({"ok": True})
        answered(orch, config_sha256(shipped()), game_uid="u-0002")
        with pytest.raises(MatchAborted) as excinfo:
            orch.agree_config(shipped(), game_uid="u-0001", timeout=0.0)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
    def test_a_digest_is_consumed_rather_than_left_for_the_next_gate(self) -> None:
        orch, _ = orchestrator({"ok": True}, {"ok": True})
        answered(orch, config_sha256(shipped()))
        orch.agree_config(shipped())
        assert orch.inboxes.digests.empty()
