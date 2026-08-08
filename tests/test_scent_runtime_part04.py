from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_runtime")).items() if not k.startswith("__")})

class TestTheBeliefMapMoves:
    def test_it_starts_uniform_over_the_free_cells(self) -> None:
        game, _ = a_subgame()
        assert game.belief.total() == pytest.approx(1.0)
        assert game.belief.concentration() == 0.0
    def test_evidence_concentrates_it(self) -> None:
        game, _ = a_subgame()
        before = game.belief.heatmap()
        game.play()
        assert game.belief.heatmap() != before
        assert game.belief.concentration() > 0.0
    def test_it_points_at_the_trail_rather_than_at_us(self) -> None:
        game, _ = a_subgame()
        game.play()
        peak = game.belief.most_likely()
        assert peak is not None
        assert abs(peak[0] - THEIR_START[0]) <= 2 and abs(peak[1] - THEIR_START[1]) <= 2
    def test_it_stays_a_distribution(self) -> None:
        game, _ = a_subgame()
        game.play()
        assert game.belief.total() == pytest.approx(1.0)
        assert all(value >= 0.0 for value in game.belief.mass.values())
    def test_an_unverifiable_field_leaves_the_belief_alone(self) -> None:
        game, _ = a_subgame(ScentedOpponent(junk=True), moves=["STAY"])
        before = game.belief.heatmap()
        game.play()
        assert game.belief.heatmap() == before
    def test_the_live_view_is_never_handed_the_true_cell(self) -> None:
        import inspect
        from cop_agent.ui.view import render
        assert "thief" not in inspect.signature(render).parameters
        assert "opponent" not in inspect.signature(render).parameters
