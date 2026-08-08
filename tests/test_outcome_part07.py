from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_outcome")).items() if not k.startswith("__")})

class TestAClaimIsCheckedBeforeItIsSent:
    def test_a_supported_claim_passes(self) -> None:
        assert claim_is_supported(board(cop=(3, 3)), AXES, (3, 3))
    def test_an_unsupported_claim_fails(self) -> None:
        assert not claim_is_supported(board(), AXES, (3, 3))
    def test_the_right_capture_at_the_wrong_cell_fails(self) -> None:
        assert not claim_is_supported(board(cop=(3, 3)), AXES, (2, 2))
    def test_over_many_random_boards_a_claim_appears_exactly_when_it_should(self) -> None:
        rng = random.Random(20260804)
        for _ in range(4000):
            cells = [(rng.randrange(6), rng.randrange(6)) for _ in range(4)]
            state = board(cop=cells[0], thief=cells[1], barriers=frozenset(cells[2:]))
            expected = (
                is_capture_by_overlap(state)
                or is_trapping_capture(state)
                or is_enclosure_capture(state, AXES)
            )
            assert (capture_claim(state, AXES) is not None) is expected
