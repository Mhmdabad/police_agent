from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_lock_negotiation")).items() if not k.startswith("__")})

class TestThePreGameLockDisclosesNothingAboutTheBoard:
    @staticmethod
    def sent(ours: Side, theirs: Side) -> dict[str, Any]:
        with pytest.raises(MatchAborted):
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        return theirs.inboxes.scent_locks.get_nowait()
    def test_the_offer_is_exactly_the_published_fixture(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        body = self.sent(ours, theirs)
        assert body == {
            SCENT_KEY: propose().terms(),
            SCENT_DIGEST_KEY: propose().digest(),
            SERIES_KEY: GAME_UID,
        }
    def test_it_says_nothing_a_commitment_would(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        wire_text = json.dumps(self.sent(ours, theirs))
        assert re.findall(r"[0-9a-f]{32,}", wire_text) == [propose().digest()]
        assert "nonce" not in wire_text and "salt" not in wire_text
    def test_the_same_bytes_are_offered_whatever_the_board_says(
        self, wire: tuple[Side, Side], tmp_path: Path
    ) -> None:
        offers = []
        for cop, thief in (((0, 0), (6, 5)), ((3, 7), (1, 1))):
            ours, theirs = fresh(wire)
            runner = a_runner(ours, parameters(), tmp_path)
            runner.start = replace(runner.start, cop=cop, thief=thief)
            offers.append(self.sent(ours, theirs))
        assert offers[0] == offers[1]
    def test_no_turn_or_scent_field_crosses_the_wire(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        self.sent(ours, theirs)
        assert theirs.inboxes.turns.empty()
        assert theirs.inboxes.accepted_turns == {}
