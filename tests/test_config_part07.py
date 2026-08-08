from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_config")).items() if not k.startswith("__")})

class TestCanonicalHashing:
    def test_key_order_does_not_change_the_digest(self) -> None:
        config = shipped()
        shuffled = dict(reversed(list(config.items())))
        assert config_sha256(config) == config_sha256(shuffled)
    def test_canonical_bytes_have_no_incidental_whitespace(self) -> None:
        sample = {"a": 1, "b": [1, 2]}
        assert b", " not in canonical_bytes(sample)
        assert b": " not in canonical_bytes(sample)
    def test_digest_is_stable(self) -> None:
        assert config_sha256(shipped()) == config_sha256(shipped())
    def test_any_change_changes_the_digest(self) -> None:
        config = copy.deepcopy(shipped())
        before = config_sha256(config)
        config["world"]["map_area"] = "London"
        assert config_sha256(config) != before
