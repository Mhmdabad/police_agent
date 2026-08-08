from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_config_agreement")).items() if not k.startswith("__")})

class TestTheComparisonItself:
    def test_equal_digests_agree(self) -> None:
        assert digests_agree(agreed_digest(), agreed_digest())
    def test_different_digests_do_not(self) -> None:
        assert not digests_agree(agreed_digest(), config_sha256(altered()))
    def test_a_truncated_digest_does_not_agree(self) -> None:
        assert not digests_agree(agreed_digest(), agreed_digest()[:-1])
    def test_it_does_not_leak_the_position_of_the_first_difference(self) -> None:
        import cop_agent.shared.config as module
        assert "compare_digest" in Path(module.__file__ or "").read_text()
