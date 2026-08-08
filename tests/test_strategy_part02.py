from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_strategy")).items() if not k.startswith("__")})

class TestPursuit:
    def test_closes_distance_from_the_corner(self) -> None:
        brain = PoliceBrain(axes=AXES)
        state = make()
        move = brain.decide(state, target=state.thief).action
        assert isinstance(move, MoveAction)
        assert move.move in {"S", "E"}
    def test_the_rulebook_worked_example(self) -> None:
        brain = PoliceBrain(axes=AXES)
        state = make(cop=(2, 2), thief=(5, 5))
        action = brain.decide(state, target=state.thief).action
        assert isinstance(action, MoveAction)
        assert action.move in {"S", "E"}
    def test_never_increases_the_distance_when_it_chooses_to_move(self) -> None:
        brain = PoliceBrain(axes=AXES)
        placements = 0
        for row in range(7):
            for col in range(7):
                state = make(cop=(row, col), thief=(6, 6))
                if is_capture_by_overlap(state):
                    continue  # already won; decide() is not defined for a finished position
                before = manhattan(state.cop, state.thief)
                action = brain.decide(state, target=state.thief).action
                win = winning_placement(state, AXES)
                if win is not None:
                    assert action == PlaceBarrier(win)
                    placements += 1
                    continue
                assert isinstance(action, MoveAction)
                after = manhattan(target_of(state.cop, action.move, AXES), state.thief)
                assert after <= before
        assert placements > 0, "the sweep never reached a winning position"
    def test_an_explicit_target_overrides_the_thief_position(self) -> None:
        brain = PoliceBrain(axes=AXES)
        action = brain.decide(make(cop=(3, 3), thief=(0, 0)), target=(6, 3)).action
        assert isinstance(action, MoveAction)
        assert action.move == "S"
    def test_a_walled_in_cop_stays(self) -> None:
        walls = frozenset({(2, 3), (4, 3), (3, 2), (3, 4)})
        action = PoliceBrain(axes=AXES).decide(make(cop=(3, 3), barriers=walls)).action
        assert action == MoveAction("STAY")
    def test_honours_the_negotiated_convention(self) -> None:
        flipped = AxisConvention(origin_corner="bottom-left")
        brain = PoliceBrain(axes=flipped)
        action = brain.decide(make(cop=(3, 3), thief=(0, 3))).action
        assert isinstance(action, MoveAction)
        assert action.move == "S"
