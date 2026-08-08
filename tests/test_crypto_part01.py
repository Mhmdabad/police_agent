from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_crypto")).items() if not k.startswith("__")})

class TestTheNonceGenerator:
    def test_it_is_the_agreed_length(self) -> None:
        assert len(nonce()) == NONCE_BYTES * 2
    def test_it_is_hexadecimal(self) -> None:
        assert set(nonce()) <= set("0123456789abcdef")
    def test_every_draw_is_different(self) -> None:
        assert len({nonce() for _ in range(2000)}) == 2000
    def test_it_comes_from_the_csprng(self, monkeypatch: pytest.MonkeyPatch) -> None:
        called: list[int] = []
        def spy(size: int) -> str:
            called.append(size)
            return "ab" * size
        monkeypatch.setattr(secrets, "token_hex", spy)
        assert nonce() == "ab" * NONCE_BYTES
        assert called == [NONCE_BYTES]
    def test_the_crypto_module_never_imports_random(self) -> None:
        source = (SRC / "domain" / "crypto.py").read_text()
        assert not re.search(r"^\s*(import random|from random import)", source, re.M)
    def test_randomness_elsewhere_is_seeded_rather_than_ambient(self) -> None:
        ambient = [
            f"{path.relative_to(SRC)}: {hit}"
            for path in sorted(SRC.rglob("*.py"))
            for hit in re.findall(r"\brandom\.(?!Random\b)\w+\(", path.read_text())
        ]
        assert ambient == []
