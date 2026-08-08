from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_config")).items() if not k.startswith("__")})

class TestBookValueAccessors:
    def test_book_value_reads_the_table(self) -> None:
        assert book_value("scoring", "capture_cop") == 20
        assert book_value("world", "map_area") == "New York"
    def test_book_int_narrows_the_type(self) -> None:
        assert book_int("movement_and_barriers", "max_barriers") == 14
    def test_book_int_refuses_a_non_integer(self) -> None:
        with pytest.raises(TypeError, match="not int"):
            book_int("pheromones", "pheromone_center_intensity")
    def test_unknown_parameter_is_refused(self) -> None:
        with pytest.raises(KeyError, match="not an Appendix F parameter"):
            book_value("scoring", "bonus_points")
    def test_domain_defaults_come_from_the_table(self) -> None:
        from cop_agent.domain.actions import DEFAULT_MAX_BARRIERS
        from cop_agent.domain.outcome import DEFAULT_SURVIVAL_THRESHOLD
        from cop_agent.domain.scoring import BOOK_SCORES, BOOK_TIE_SCORE, Outcome
        assert book_int("movement_and_barriers", "max_barriers") == DEFAULT_MAX_BARRIERS
        assert book_int("movement_and_barriers", "survival_threshold") == DEFAULT_SURVIVAL_THRESHOLD
        assert BOOK_SCORES[Outcome.CAPTURE] == (
            book_int("scoring", "capture_cop"),
            book_int("scoring", "capture_thief"),
        )
        assert book_int("scoring", "tie_score") == BOOK_TIE_SCORE
