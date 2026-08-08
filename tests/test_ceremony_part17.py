from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestUnprovableIsReportedSeparatelyFromProven:
    def test_a_commitment_never_revealed(self) -> None:
        match, disclosed, states = honest_match()
        match.steps[2].revealed_theirs = None
        result = audit_opponent(match, disclosed, states)
        assert "never revealed" in result.failures[0]
    def test_a_commitment_with_no_nonce_disclosed(self) -> None:
        match, disclosed, states = honest_match()
        thin = FinalReveal("thief", {k: v for k, v in disclosed.nonces.items() if k != 2}, WHEN)
        assert "no nonce disclosed" in audit_opponent(match, thin, states).failures[0]
    def test_a_step_we_cannot_rebuild_the_board_for(self) -> None:
        match, disclosed, states = honest_match()
        del states[3]
        assert "no board state" in audit_opponent(match, disclosed, states).failures[0]
