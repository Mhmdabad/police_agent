from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_rehandshake_between_subgames")).items() if not k.startswith("__")})

class TestTwoRealPeersPlayASixSubGameSeriesAcrossFiveBoundaries:
    def test_both_sides_played_all_six(self, series: tuple[Live, Live]) -> None:
        for side in series:
            assert [o.number for o in side.runner.outcomes] == list(range(1, BOOK_SERIES + 1))
    def test_neither_side_deadlocked_re_handshaking_against_the_other(
        self, series: tuple[Live, Live]
    ) -> None:
        for side in series:
            assert side.runner.peering is not None
            assert side.runner.peering.sub_game == BOOK_SERIES
    def test_nothing_was_rejected_at_either_door(self, series: tuple[Live, Live]) -> None:
        for side in series:
            assert side.inboxes.rejected == []
    def test_no_boundary_had_to_be_retried_into(self, series: tuple[Live, Live]) -> None:
        for side in series:
            assert side.inboxes.deferred == []
    def test_every_sub_game_audited_clean(self, series: tuple[Live, Live]) -> None:
        for side in series:
            assert side.runner.opponent_played_fairly, side.runner.failures()
    def test_the_scent_lock_survives_every_boundary(self, series: tuple[Live, Live]) -> None:
        us, them = series
        assert us.runner.scent_lock is not None
        assert us.runner.scent_lock == them.runner.scent_lock
    def test_the_config_digest_is_still_the_one_both_sides_agreed(
        self, series: tuple[Live, Live]
    ) -> None:
        us, them = series
        digest = config_sha256(parameters())
        for side in (us, them):
            assert {log.config_sha256 for log in self.logs(side)} == {digest}
    @staticmethod
    def logs(side: Live) -> list[MatchLog]:
        return [outcome.log for outcome in side.runner.outcomes]
    def test_every_log_is_numbered_for_its_own_sub_game(self, series: tuple[Live, Live]) -> None:
        for side in series:
            assert [log.sub_game for log in self.logs(side)] == list(range(1, BOOK_SERIES + 1))
            assert {log.game_uid for log in self.logs(side)} == {GAME_UID}
    def test_every_log_stamps_verified_ok(self, series: tuple[Live, Live], tmp_path: Path) -> None:
        for side in series:
            for log in self.logs(side):
                written = log.write(tmp_path / f"{side.role}-{log.sub_game}")
                assert walk(load(written)).stamp is Stamp.VERIFIED_OK, str(log.sub_game)
    def test_the_turn_ledger_was_reset_per_sub_game_and_nothing_was_dropped(
        self, series: tuple[Live, Live]
    ) -> None:
        for side in series:
            assert side.inboxes.duplicates == []
            assert sorted(self.logs(side)[0].entries) == list(range(1, STEPS + 1))
    def test_the_artefacts_of_the_whole_series_are_coherent(
        self, series: tuple[Live, Live], tmp_path: Path
    ) -> None:
        from test_localhost_match import REPOS
        for side in series:
            runner = side.runner
            result = runner.result("a" * 40, 0, agreed=False, repositories=REPOS)
            artefacts = runner.artefacts(result)
            assert len(artefacts.configs) == BOOK_SERIES
            assert len(artefacts.logs) == BOOK_SERIES
            assert artefacts.check().coherent, str(artefacts.check())
    def test_the_declaration_records_the_addresses_the_last_boundary_agreed(
        self, series: tuple[Live, Live]
    ) -> None:
        for side in series:
            written = json.loads(
                (side.runner.directory / f"declaration_{GAME_ID}.json").read_text()
            )
            for role in (ROLE, OPPONENT):
                assert written["mcp_addresses"][role]["since_sub_game"] == BOOK_SERIES
    def test_the_two_sides_stayed_in_separate_processes_sharing_only_the_wire(
        self, series: tuple[Live, Live]
    ) -> None:
        us, them = series
        assert us.inboxes is not them.inboxes
        assert us.runner.orchestrator.client is not them.runner.orchestrator.client
