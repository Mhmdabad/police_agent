from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_outcome")).items() if not k.startswith("__")})

class TestSurvival:
    def test_default_threshold_matches_appendix_f(self) -> None:
        assert DEFAULT_SURVIVAL_THRESHOLD == 35
    def test_not_survived_before_the_threshold(self) -> None:
        assert not is_survival(make(step=34), AXES)
    def test_survived_at_the_threshold(self) -> None:
        assert is_survival(make(step=35), AXES)
    def test_survived_beyond_the_threshold(self) -> None:
        assert is_survival(make(step=40), AXES)
    def test_threshold_is_raisable_by_agreement(self) -> None:
        assert not is_survival(make(step=35), AXES, survival_threshold=50)
        assert is_survival(make(step=50), AXES, survival_threshold=50)
    def test_capture_by_overlap_denies_survival(self) -> None:
        assert not is_survival(make(cop=(3, 3), thief=(3, 3), step=40), AXES)
    def test_trapping_capture_denies_survival(self) -> None:
        state = make(thief=(3, 3), barriers=frozenset({(3, 3)}), step=40)
        assert not is_survival(state, AXES)
    def test_enclosure_capture_denies_survival(self) -> None:
        walls = frozenset({(2, 3), (4, 3), (3, 2), (3, 4)})
        assert not is_survival(make(thief=(3, 3), barriers=walls, step=40), AXES)
    def test_counts_full_turns_not_half_moves(self) -> None:
        state = make(step=34)
        state = apply_move(state, "cop", "S", AXES)
        state = apply_move(state, "thief", "N", AXES)
        assert not is_survival(state, AXES)
        assert is_survival(advance_turn(state), AXES)
