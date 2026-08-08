from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestAPartialRevealIsRefused:
    def test_a_step_with_no_recorded_nonce_stops_the_reveal(self) -> None:
        match = played(steps=2)
        match.at(7)  # opened but never committed
        match.finish()
        with pytest.raises(CeremonyError, match=r"no nonce recorded for step\(s\) \[7\]"):
            match.final_reveal(WHEN)
    def test_their_reveal_must_cover_every_step_they_committed_to(self) -> None:
        match = MatchCeremony(role="police")
        for step in (1, 2):
            match.at(step).receive(their_commitment(step=step))
        with pytest.raises(CeremonyError, match=r"omits step\(s\) \[2\]"):
            match.receive_final_reveal(
                FinalReveal(sender="thief", nonces={1: THEIR_NONCE}, timestamp=WHEN)
            )
    def test_extra_steps_in_their_reveal_are_tolerated(self) -> None:
        match = MatchCeremony(role="police")
        match.at(1).receive(their_commitment(step=1))
        disclosed = FinalReveal(
            sender="thief", nonces={1: THEIR_NONCE, 9: THEIR_NONCE}, timestamp=WHEN
        )
        assert match.receive_final_reveal(disclosed) is disclosed
    def test_a_final_reveal_from_the_wrong_role_is_refused(self) -> None:
        match = MatchCeremony(role="police")
        with pytest.raises(CeremonyError, match="expected 'thief'"):
            match.receive_final_reveal(FinalReveal(sender="police", nonces={}, timestamp=WHEN))
