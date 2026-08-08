from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tradeoff")).items() if not k.startswith("__")})

class TestTheComparison:
    def test_a_bigger_cut_than_the_step_is_taken(self) -> None:
        assert call(placement=BarrierScore((1, 1), 5, 0, False), move_gain=1).place
    def test_an_equal_trade_goes_to_the_move(self) -> None:
        assert not call(placement=BarrierScore((1, 1), 1, 0, False), move_gain=1).place
    def test_a_smaller_cut_is_refused(self) -> None:
        assert not call(placement=BarrierScore((1, 1), 1, 0, False), move_gain=2).place
    def test_the_budget_bar_applies_on_top(self) -> None:
        beats_the_move = call(placement=BarrierScore((1, 1), 2, 0, False), move_gain=1)
        assert beats_the_move.place
        assert not call(placement=BarrierScore((1, 1), 2, 0, False), move_gain=1, required=6).place
    def test_no_permitted_placement_means_move(self) -> None:
        assert not call(placement=None).place
    def test_the_reserve_refuses_however_good_the_trade(self) -> None:
        held = call(
            placement=BarrierScore((1, 1), 40, 0, False),
            move_gain=1,
            used=DEFAULT_MAX_BARRIERS - RESERVE,
        )
        assert not held.affordable
        assert not held.place
    def test_the_endgame_releases_it(self) -> None:
        released = call(
            placement=BarrierScore((1, 1), 40, 0, False),
            move_gain=1,
            used=DEFAULT_MAX_BARRIERS - RESERVE,
            endgame=True,
        )
        assert released.place
