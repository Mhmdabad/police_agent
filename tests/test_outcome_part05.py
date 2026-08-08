from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_outcome")).items() if not k.startswith("__")})

class TestTechnicalLoss:
    def test_scores_zero_for_both_sides(self) -> None:
        assert technical_loss_scores() == (0, 0)
    def test_symmetry_removes_the_incentive_to_stall(self) -> None:
        cop, thief = technical_loss_scores()
        assert cop == thief == 0
    def test_covers_the_four_causes_the_rulebook_names(self) -> None:
        assert {c.value for c in TechnicalLoss} == {
            "crash",
            "timeout",
            "forgery",
            "illegal_action",
        }
    def test_causes_are_distinct(self) -> None:
        assert len(set(TechnicalLoss)) == 4
    def test_is_not_derived_from_the_board(self) -> None:
        import cop_agent.domain.outcome as outcome
        assert not hasattr(outcome, "is_technical_loss")
    def test_a_winning_board_still_scores_zero(self) -> None:
        won = make(step=40)
        assert is_survival(won, AXES)
        assert technical_loss_scores() == (0, 0)
