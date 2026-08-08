from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_over_the_wire")).items() if not k.startswith("__")})

class TestBothSidesAuditEachOtherClean:
    def test_an_honest_match_produces_no_findings(self, played: tuple[Side, Side]) -> None:
        for side in played:
            result = side.game.audit()
            assert result.clean, f"{side.role}: {result}"
            assert result.checked == STEPS
    def test_nothing_was_rejected_at_either_door(self, played: tuple[Side, Side]) -> None:
        for side in played:
            assert side.inboxes.rejected == []
    def test_the_log_carries_the_field_the_commitment_covers(
        self, played: tuple[Side, Side]
    ) -> None:
        cop, _ = played
        for step in range(1, STEPS + 1):
            entry = cop.game.log.entries[step]
            assert entry.reveal is not None
            assert entry.reveal["scent"] == cop.sent[step - 1]
