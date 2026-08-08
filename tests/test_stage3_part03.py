from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage3")).items() if not k.startswith("__")})

class TestQuotaNeverExceeded:
    def test_a_full_match_stays_within_the_quota(self) -> None:
        state = make(cop=(0, 0), thief=(3, 3))
        brain = PoliceBrain(axes=AXES)
        turns = 0
        for step in range(35):
            if evaluate(state, AXES) is not Outcome.ONGOING:
                break
            state = apply_action(state, "cop", brain.decide(state, target=state.thief).action, AXES)
            state = evade(replace(state, step=step + 1))
            turns += 1
            assert state.barriers_used <= DEFAULT_MAX_BARRIERS
        assert turns > 20, f"the match ended after {turns} turns and proved little"
    def test_an_open_board_match_spends_nothing(self) -> None:
        state = make(cop=(0, 0), thief=(3, 3))
        brain = PoliceBrain(axes=AXES)
        placements = 0
        for step in range(35):
            if evaluate(state, AXES) is not Outcome.ONGOING:
                break
            action = brain.decide(state, target=state.thief).action
            placements += isinstance(action, PlaceBarrier)
            state = apply_action(state, "cop", action, AXES)
            state = evade(replace(state, step=step + 1))
        assert placements == 0
    def test_a_cop_that_always_places_still_cannot_exceed_the_quota(self) -> None:
        for limit in (4, 7, 14, 20):
            state = make(cop=(3, 3), thief=(0, 0))
            brain = PoliceBrain(axes=AXES, max_barriers=limit)
            placed = 0
            for _ in range(60):
                budget = Budget(used=state.barriers_used, limit=limit)
                if not budget.may_spend(looks_like_endgame(state, AXES, state.thief)):
                    break
                best = best_placement(state, AXES, state.thief)
                if best is None:
                    break
                state = apply_action(state, "cop", PlaceBarrier(best.at), AXES, max_barriers=limit)
                placed += 1
                assert state.barriers_used <= limit
                options = legal_moves(state, "cop", AXES)
                if not options:
                    break
                state = apply_action(
                    state,
                    "cop",
                    MoveAction(brain._pick_move(state, target=state.thief)),
                    AXES,
                    max_barriers=limit,
                )
            assert placed > 0, f"limit {limit} never placed anything"
            assert state.barriers_used <= limit
    def test_and_stops_before_breaching_the_reserve(self) -> None:
        state = make(cop=(3, 3), thief=(0, 0))
        brain = PoliceBrain(axes=AXES)
        for _ in range(60):
            if looks_like_endgame(state, AXES, state.thief):
                return
            if not Budget(used=state.barriers_used).may_spend(endgame=False):
                break
            best = best_placement(state, AXES, state.thief)
            if best is None:
                break
            state = apply_action(state, "cop", PlaceBarrier(best.at), AXES)
            assert state.barriers_used <= DEFAULT_MAX_BARRIERS - RESERVE
            if not legal_moves(state, "cop", AXES):
                break
            state = apply_action(
                state, "cop", MoveAction(brain._pick_move(state, target=state.thief)), AXES
            )
        assert state.barriers_used == DEFAULT_MAX_BARRIERS - RESERVE
    def test_placement_stops_rather_than_erroring_when_the_quota_runs_out(self) -> None:
        walls = frozenset({(6, col) for col in range(7)})
        state = make(cop=(2, 1), thief=(2, 5), barriers=walls)
        spent = PoliceBrain(axes=AXES, max_barriers=7)
        assert state.barriers_used == 7
        action = spent.decide(state, target=state.thief).action
        assert isinstance(action, MoveAction)
