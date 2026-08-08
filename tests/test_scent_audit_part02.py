from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_audit")).items() if not k.startswith("__")})

class TestTheTrailIsRederivedFromTheMovementHistory:
    def test_a_stationary_agent_re_emits_at_full_strength(self) -> None:
        fields = trail_snapshots([(4, 4), (4, 4), (4, 4)], BOARD)
        assert [field["4,4"] for field in fields] == [CENTRE_INTENSITY] * 3
    def test_decay_happens_exactly_once_per_full_turn(self) -> None:
        fields = trail_snapshots([(4, 4), (0, 0), (0, 0)], BOARD)
        assert fields[1]["4,4"] == pytest.approx(CENTRE_INTENSITY * RETENTION, abs=5e-4)
        assert fields[2]["4,4"] == pytest.approx(CENTRE_INTENSITY * RETENTION**2, abs=5e-4)
    def test_it_agrees_with_what_a_live_peer_actually_emits(self) -> None:
        memory = ScentMemory()
        live = []
        for cell in [(6, 5), (6, 4), (5, 4)]:
            memory.emit(cell, BOARD)
            live.append(memory.outgoing())
            memory.decay()
        assert live == trail_snapshots([(6, 5), (6, 4), (5, 4)], BOARD)
    def test_positions_come_from_the_revealed_moves(self) -> None:
        plays = [
            StepPlay(n, MoveAction(ours), MoveAction(theirs), None)  # type: ignore[arg-type]
            for n, (ours, theirs) in enumerate(zip(OUR_STEP, THEIR_MOVES, strict=False), start=1)
        ]
        assert replay(START, AXES, OUR_ROLE, plays) == EXPECTED_REPLAY
    def test_a_barrier_turn_leaves_the_placer_where_it_stands(self) -> None:
        assert replay(START, AXES, OUR_ROLE, [BARRIER_PLAY]) == BARRIER_EXPECT
