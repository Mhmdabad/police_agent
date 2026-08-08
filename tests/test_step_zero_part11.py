from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_step_zero")).items() if not k.startswith("__")})

class TestWhatIsSignedIsNotWhatIsSent:
    def test_the_statement_excludes_the_signature(self, tmp_path: Path) -> None:
        declared = declaration(tmp_path)
        content = statement(declared.hardware, declared.provenance)
        assert "signature" not in content
        assert set(declared.to_dict()) == {"hardware", "provenance", "signature"}
    def test_the_key_is_never_read_from_a_file_in_this_repository(self) -> None:
        source = (Path(__file__).parents[1] / "src/cop_agent/infra/step_zero.py").read_text()
        assert "environ.get(SIGNING_KEY_ENV)" in source.replace("source.", "environ.")
        assert "open(" not in source
        for tracked in (Path(__file__).parents[1] / "config").rglob("*"):
            if tracked.is_file():
                assert SIGNING_KEY_ENV not in tracked.read_text()
