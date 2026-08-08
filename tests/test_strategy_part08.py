from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_strategy")).items() if not k.startswith("__")})

class TestContainmentTieBreak:
    def test_distance_still_dominates(self) -> None:
        brain = PoliceBrain(axes=AXES)
        state = make(cop=(0, 0), thief=(0, 6))
        action = brain.decide(state, target=state.thief).action
        assert isinstance(action, MoveAction)
        assert action.move == "E"
    def test_a_tie_is_broken_not_left_to_position(self) -> None:
        brain = PoliceBrain(axes=AXES)
        state = make(cop=(2, 2), thief=(5, 5))
        action = brain.decide(state, target=state.thief).action
        assert isinstance(action, MoveAction)
        assert action.move in {"S", "E"}
    def test_it_prefers_shrinking_the_thiefs_reachable_area(self) -> None:
        walls = frozenset({(0, 2), (1, 2), (3, 2), (4, 2), (5, 2), (6, 2)})
        state = make(cop=(2, 1), thief=(2, 5), barriers=walls)
        assert PoliceBrain(axes=AXES)._pick_move(state, target=state.thief) == "E"
    def test_but_a_barrier_on_the_corridor_beats_the_step(self) -> None:
        walls = frozenset({(0, 2), (1, 2), (3, 2), (4, 2), (5, 2), (6, 2)})
        state = make(cop=(2, 1), thief=(2, 5), barriers=walls)
        assert reachable_area(state, (2, 5), AXES) == 43
        call = weigh(state, AXES, (2, 5), "E")
        assert call.placement is not None
        assert call.placement.at == (2, 1)
        assert (call.placement_value, call.move_gain) == (14, 1)
        assert call.place
        assert PoliceBrain(axes=AXES).decide(state, target=state.thief).action == PlaceBarrier(
            (2, 1)
        )
    def test_edge_pressure_prefers_a_cornered_target(self) -> None:
        brain = PoliceBrain(axes=AXES)
        assert brain._edge_pressure(make(), (0, 0)) == 0
        assert brain._edge_pressure(make(), (3, 3)) == 3
        assert brain._edge_pressure(make(), (0, 3)) == 0
    def test_edge_pressure_is_symmetric_across_the_board(self) -> None:
        brain = PoliceBrain(axes=AXES)
        assert brain._edge_pressure(make(), (6, 6)) == 0
        assert brain._edge_pressure(make(), (1, 1)) == 1
    def test_the_ranking_is_total(self) -> None:
        brain = PoliceBrain(axes=AXES)
        state = make(cop=(3, 3), thief=(3, 3))
        ranks = [brain._rank(state, move, state.thief) for move in brain.options(state)]
        assert len(set(ranks)) == len(ranks)
    def test_it_stays_deterministic_across_instances(self) -> None:
        state = make(cop=(2, 2), thief=(5, 5))
        first = PoliceBrain(axes=AXES).decide(state).action
        second = PoliceBrain(axes=AXES).decide(state).action
        assert first == second
    def test_it_never_returns_an_illegal_move(self) -> None:
        brain = PoliceBrain(axes=AXES)
        walls = frozenset({(1, 1), (2, 2), (4, 4)})
        for row in range(7):
            for col in range(7):
                state = make(cop=(row, col), thief=(6, 0), barriers=walls)
                if state.is_barrier(state.cop):
                    continue
                action = brain.decide(state).action
                if isinstance(action, PlaceBarrier):
                    assert action.at in placement_range(state, AXES)
                else:
                    assert action.move in brain.options(state)
