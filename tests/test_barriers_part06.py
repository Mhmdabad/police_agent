from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_barriers")).items() if not k.startswith("__")})

class TestSelfPreservationConstraint:
    def test_a_placement_that_disconnects_us_from_the_target_is_refused(self) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(1, 0)})
        refused = next(s for s in rank_placements(state, AXES, (2, 2)) if s.at == (0, 1))
        assert refused.disconnects
        assert not refused.permitted
        assert (0, 1) not in {s.at for s in safe_placements(state, AXES, (2, 2))}
    def test_the_refused_placement_was_the_better_looking_one(self) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(1, 0)})
        refused = next(s for s in rank_placements(state, AXES, (2, 2)) if s.at == (0, 1))
        chosen = best_placement(state, AXES, (2, 2))
        assert chosen is not None and chosen.at == (0, 0)
        assert refused.escape_reduction > chosen.escape_reduction
    def test_a_placement_leaving_no_legal_move_is_refused(self) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(0, 1), (1, 0)})
        assert legal_moves(state, "cop", AXES) == ["STAY"]
        only = rank_placements(state, AXES, (2, 2))[0]
        assert only.at == (0, 0)
        assert only.immobilises
        assert not only.permitted
    def test_refusing_everything_means_placing_nothing(self) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(0, 1), (1, 0)})
        assert rank_placements(state, AXES, (2, 2)) != []
        assert safe_placements(state, AXES, (2, 2)) == []
        assert best_placement(state, AXES, (2, 2)) is None
    def test_immobilising_outranks_disconnecting_in_the_veto_reason(self) -> None:
        both = BarrierScore(
            at=(0, 0), escape_reduction=9, chain=4, disconnects=True, immobilises=True
        )
        assert both.veto == "NO-LEGAL-MOVE-AFTER"
    def test_a_permitted_placement_has_no_veto_string(self) -> None:
        state = board((3, 3), (5, 5))
        assert all(s.veto == "" and s.permitted for s in safe_placements(state, AXES, (5, 5)))
    def test_the_penalty_applies_to_either_veto(self) -> None:
        stuck = BarrierScore(
            at=(0, 0), escape_reduction=48, chain=4, disconnects=False, immobilises=True
        )
        assert stuck.total < 0
        assert not stuck.permitted
    def test_a_refused_candidate_is_still_scored_and_logged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(1, 0)})
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.barriers"):
            best_placement(state, AXES, (2, 2))
        assert "(0, 1)" in caplog.text
        assert "CUTS-SELF-OFF" in caplog.text
    def test_having_no_permitted_placement_is_logged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(0, 1), (1, 0)})
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.barriers"):
            best_placement(state, AXES, (2, 2))
        assert "every candidate is refused" in caplog.text
    def test_the_open_board_is_unaffected(self) -> None:
        state = board((3, 3), (5, 5))
        assert len(safe_placements(state, AXES, (5, 5))) == 5
