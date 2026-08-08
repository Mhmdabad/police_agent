from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_bluff")).items() if not k.startswith("__")})

class TestSelfConsistency:
    @staticmethod
    def trail_through(*cells: tuple[int, int]) -> dict[tuple[int, int], float]:
        laid = Trail()
        for cell in cells:
            laid.deposit(emission(cell, BOARD.grid_size))
            laid.decay()
        return laid.values
    def test_a_claim_our_own_scent_refutes_is_refused(self) -> None:
        here = self.trail_through((5, 1))
        far = Bluff(intent="lie", text="north", about=(0, 6))
        with pytest.raises(SelfContradictionError, match="convict on arrival"):
            vet(far, here)
    def test_a_claim_our_own_scent_supports_is_allowed(self) -> None:
        walked = self.trail_through((0, 5), (5, 1))
        assert vet(Bluff(intent="lie", text="north", about=(0, 5)), walked)
    def test_truthful_hints_are_never_vetted(self) -> None:
        honest = Bluff(intent="truth", text="south", about=(5, 1))
        assert vet(honest, {}) is honest
    def test_it_is_the_opponents_own_detector_pointed_at_us(self) -> None:
        assert contradicts_our_field(
            Bluff(intent="lie", text="x", about=(0, 6)), self.trail_through((5, 1)), 0.81
        )
    def test_a_plausible_decoy_aims_at_our_own_history(self) -> None:
        walked = self.trail_through((0, 5), (5, 1))
        assert plausible_decoy((5, 1), BOARD, walked) == (0, 5)
    def test_with_no_trail_it_falls_back_and_the_guard_refuses(self) -> None:
        assert plausible_decoy((5, 1), BOARD, {}) == decoy((5, 1), BOARD)
    def test_speak_uses_the_credible_decoy_when_given_a_field(self) -> None:
        walked = self.trail_through((0, 5), (5, 1))
        assert speak((5, 1), BOARD, (3, 3), "lie", own_field=walked).about == (0, 5)
    def test_it_is_stable_across_calls(self) -> None:
        walked = self.trail_through((0, 5), (5, 1))
        assert plausible_decoy((5, 1), BOARD, walked) == plausible_decoy((5, 1), BOARD, walked)
