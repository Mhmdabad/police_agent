from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_actions")).items() if not k.startswith("__")})

class TestBarrierQuota:
    def test_default_quota_matches_appendix_f(self) -> None:
        assert DEFAULT_MAX_BARRIERS == 14
    def _spend(self, quota: int) -> BoardState:
        state = make(cop=(0, 0), thief=(6, 6))
        for i in range(quota):
            state = place_barrier(state, (1, state.cop[1]), AXES, max_barriers=quota)
            if i < quota - 1:
                state = apply_action(state, "cop", MoveAction("E"), AXES, max_barriers=quota)
        return state
    def test_placing_up_to_the_quota_is_allowed(self) -> None:
        assert self._spend(6).barriers_used == 6
    def test_one_past_the_quota_is_refused(self) -> None:
        state = self._spend(6)
        with pytest.raises(IllegalActionError, match="quota exhausted"):
            place_barrier(state, (0, 6), AXES, max_barriers=6)
    def test_quota_is_raisable_by_agreement(self) -> None:
        state = self._spend(6)
        assert place_barrier(state, (0, 6), AXES, max_barriers=20).barriers_used == 7
    def test_quota_applies_through_apply_action(self) -> None:
        state = self._spend(6)
        with pytest.raises(IllegalActionError, match="quota exhausted"):
            apply_action(state, "cop", PlaceBarrier((0, 6)), AXES, max_barriers=6)
