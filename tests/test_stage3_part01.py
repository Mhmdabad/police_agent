from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage3")).items() if not k.startswith("__")})

class TestNeverIllegal:
    def test_the_policy_output_is_always_legal(self) -> None:
        rng = random.Random(50)
        cells = [(row, col) for row in range(7) for col in range(7)]
        moved = placed = 0
        for _ in range(400):
            walls = frozenset(rng.sample(cells, rng.randint(0, 13)))
            free = [cell for cell in cells if cell not in walls]
            if len(free) < 2:
                continue
            state = make(cop=rng.choice(free), thief=rng.choice(free), barriers=walls)
            if is_capture_by_overlap(state) or is_trapping_capture(state):
                continue
            if not legal_moves(state, "cop", AXES):
                with pytest.raises(NoLegalActionError):
                    PoliceBrain(axes=AXES).decide(state, target=state.thief)
                continue
            action = PoliceBrain(axes=AXES).decide(state, target=state.thief).action
            if isinstance(action, PlaceBarrier):
                assert action.at in placement_range(state, AXES)
                assert not state.is_barrier(action.at)
                placed += 1
            else:
                assert action.move in legal_moves(state, "cop", AXES)
                moved += 1
            apply_action(state, "cop", action, AXES)
        assert moved > 0 and placed > 0, f"moved={moved} placed={placed}"
    def test_a_sealed_in_cop_raises_rather_than_inventing_a_move(self) -> None:
        walls = frozenset({(2, 3), (4, 3), (3, 2), (3, 4), (3, 3)})
        with pytest.raises(NoLegalActionError, match="no legal move"):
            PoliceBrain(axes=AXES).decide(make(cop=(3, 3), thief=(0, 0), barriers=walls))
