from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestRevealingIsGatedOnTheLock:
    def test_a_locked_pair_may_reveal(self) -> None:
        ceremony = both_locked()
        assert ceremony.reveal(reveal()) is ceremony.revealed_ours
    @pytest.mark.parametrize("build", [StepCeremony, lambda **k: opened()])
    def test_revealing_before_the_lock_is_refused(self, build: object) -> None:
        ceremony = build(step=4, role="police")  # type: ignore[operator]
        with pytest.raises(CeremonyError, match="before both sides are locked"):
            ceremony.reveal(reveal())
    def test_the_error_names_what_is_still_missing(self) -> None:
        ceremony = opened()
        ceremony.acknowledge(WHEN)
        with pytest.raises(CeremonyError, match="missing their acknowledgement"):
            ceremony.reveal(reveal())
    def test_a_second_reveal_is_refused(self) -> None:
        ceremony = both_locked()
        ceremony.reveal(reveal())
        with pytest.raises(CeremonyError, match="not revisable"):
            ceremony.reveal(reveal(move="S"))
    def test_a_reveal_from_the_wrong_role_is_refused(self) -> None:
        with pytest.raises(CeremonyError, match="expected 'police'"):
            both_locked().reveal(reveal(sender="thief"))
