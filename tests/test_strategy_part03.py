from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_strategy")).items() if not k.startswith("__")})

class TestLegalityGuard:
    def test_the_policy_never_returns_an_illegal_move(self) -> None:
        brain = PoliceBrain(axes=AXES)
        walls = frozenset({(1, 1), (2, 2), (3, 3), (4, 4)})
        for row in range(7):
            for col in range(7):
                state = make(cop=(row, col), thief=(6, 6), barriers=walls)
                if state.is_barrier(state.cop):
                    continue
                action = brain.decide(state).action
                if isinstance(action, PlaceBarrier):
                    assert action.at in placement_range(state, AXES)
                    assert not state.is_barrier(action.at)
                else:
                    assert action.move in brain.options(state)
    def test_a_rogue_subclass_is_caught(self) -> None:
        class Rogue(PoliceBrain):
            def _pick_move(self, state: BoardState, **context: object) -> Move:
                return "N"
        with pytest.raises(NoLegalActionError, match="not among"):
            state = make(cop=(0, 0))
            Rogue(axes=AXES).decide(state, target=state.thief)
    def test_the_base_default_relocates(self) -> None:
        class MoveOnly(BrainBase):
            @property
            def role(self) -> Agent:
                return "cop"
            def _pick_move(self, state: BoardState, **context: object) -> Move:
                return "STAY"
        assert MoveOnly(axes=AXES).decide(make()).action == MoveAction("STAY")
    def test_the_guard_cannot_be_bypassed_by_overriding_pick_move(self) -> None:
        assert "_guard" in BrainBase.decide.__code__.co_names
    def test_a_sealed_cop_has_nothing_legal(self) -> None:
        walls = frozenset({(3, 3), (2, 3), (4, 3), (3, 2), (3, 4)})
        with pytest.raises(NoLegalActionError, match="no legal move"):
            PoliceBrain(axes=AXES).decide(make(cop=(3, 3), barriers=walls))
    def test_the_guard_reports_an_empty_option_set(self) -> None:
        class Stubborn(PoliceBrain):
            def _pick_move(self, state: BoardState, **context: object) -> Move:
                return "N"
        walls = frozenset({(3, 3), (2, 3), (4, 3), (3, 2), (3, 4)})
        with pytest.raises(NoLegalActionError, match="has no legal move"):
            Stubborn(axes=AXES).decide(make(cop=(3, 3), barriers=walls))
    def test_a_legal_placement_passes(self) -> None:
        PoliceBrain(axes=AXES)._guard(make(cop=(0, 0)), PlaceBarrier((1, 0)))
    def test_a_placement_out_of_reach_is_refused(self) -> None:
        with pytest.raises(NoLegalActionError, match="illegal barrier"):
            PoliceBrain(axes=AXES)._guard(make(cop=(0, 0)), PlaceBarrier((5, 5)))
    def test_a_placement_off_the_board_is_refused(self) -> None:
        with pytest.raises(NoLegalActionError, match="illegal barrier"):
            PoliceBrain(axes=AXES)._guard(make(cop=(0, 0)), PlaceBarrier((-1, 0)))
    def test_a_placement_on_an_existing_barrier_is_refused(self) -> None:
        state = make(cop=(0, 0), barriers=frozenset({(1, 0)}))
        with pytest.raises(NoLegalActionError, match="illegal barrier"):
            PoliceBrain(axes=AXES)._guard(state, PlaceBarrier((1, 0)))
    def test_a_placement_beyond_the_quota_is_refused(self) -> None:
        walls = frozenset({(6, col) for col in range(7)})
        state = make(cop=(0, 0), barriers=walls)
        brain = PoliceBrain(axes=AXES, max_barriers=7)
        with pytest.raises(NoLegalActionError, match="illegal barrier"):
            brain._guard(state, PlaceBarrier((1, 0)))
    def test_the_guard_never_lets_an_illegal_action_through(self) -> None:
        rng = random.Random(47)
        cells = [(row, col) for row in range(7) for col in range(7)]
        brain = PoliceBrain(axes=AXES)
        rejected_moves = rejected_placements = 0
        for _ in range(200):
            walls = frozenset(rng.sample(cells, rng.randint(0, 20)))
            free = [cell for cell in cells if cell not in walls]
            state = make(cop=rng.choice(free), thief=rng.choice(free), barriers=walls)
            legal = legal_moves(state, "cop", AXES)
            reach = placement_range(state, AXES)
            for move in MOVES:
                if move in legal:
                    brain._guard(state, MoveAction(move))
                else:
                    rejected_moves += 1
                    with pytest.raises(NoLegalActionError):
                        brain._guard(state, MoveAction(move))
            affordable = state.barriers_used < brain.max_barriers
            for cell in cells:
                permitted = affordable and cell in reach and not state.is_barrier(cell)
                if permitted:
                    brain._guard(state, PlaceBarrier(cell))
                else:
                    rejected_placements += 1
                    with pytest.raises(NoLegalActionError):
                        brain._guard(state, PlaceBarrier(cell))
        assert rejected_moves > 0 and rejected_placements > 0
    def test_the_guard_agrees_with_the_domain_by_construction(self) -> None:
        state = make(cop=(3, 3), barriers=frozenset({(3, 4)}))
        for cell in ((3, 4), (0, 0), (3, 3), (2, 3)):
            try:
                place_barrier(state, cell, AXES)
            except IllegalActionError:
                with pytest.raises(NoLegalActionError):
                    PoliceBrain(axes=AXES)._guard(state, PlaceBarrier(cell))
            else:
                PoliceBrain(axes=AXES)._guard(state, PlaceBarrier(cell))
