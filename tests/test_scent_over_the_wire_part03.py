from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_over_the_wire")).items() if not k.startswith("__")})

class TestTheReceiverActuallyUsesIt:
    def test_the_opponents_trail_is_absorbed(self, played: tuple[Side, Side]) -> None:
        cop, _ = played
        assert cop.game.scent.opponent.values
        peak = cop.game.scent.opponent.strongest()
        assert peak is not None
        assert peak[1] == THIEF_START[1]  # the thief marched north, never sideways
    def test_our_own_field_is_never_absorbed_as_theirs(self, played: tuple[Side, Side]) -> None:
        cop, _ = played
        assert cop.game.scent.own.values
        assert all(cell[1] <= 2 for cell in cop.game.scent.own.values)
        assert all(cell[1] >= 3 for cell in cop.game.scent.opponent.values)
    def test_the_belief_heatmap_moved(self, played: tuple[Side, Side]) -> None:
        for side in played:
            assert side.game.belief.concentration() > 0.0
            assert side.game.belief.total() == pytest.approx(1.0)
    def test_the_belief_points_at_the_opponent_rather_than_at_us(
        self, played: tuple[Side, Side]
    ) -> None:
        cop, thief = played
        cop_peak, thief_peak = cop.game.belief.most_likely(), thief.game.belief.most_likely()
        assert cop_peak is not None and thief_peak is not None
        assert cop_peak[1] >= 3  # the thief's column, not the cop's
        assert thief_peak[1] <= 2  # the cop's column, not the thief's
    def test_the_live_view_never_receives_the_true_cell(self) -> None:
        import inspect
        from cop_agent.ui.view import render
        assert set(inspect.signature(render).parameters) == {
            "state",
            "belief",
            "role",
            "ours",
            "our_glyph",
            "opponent_glyph",
        }
