from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_replay")).items() if not k.startswith("__")})

class TestUnopenableIsNotTampered:
    def test_a_step_with_no_nonce_is_unverifiable_rather_than_failed(self, tmp_path: Path) -> None:
        checked = check_step(load(written(tmp_path, unopened=1)).seek(4))
        assert not checked.verified
        assert "cannot be opened (no nonce)" in checked.reason
    def test_a_step_with_no_reveal_says_so(self, tmp_path: Path) -> None:
        path = written(tmp_path)
        body = json.loads(path.read_text())
        body["steps"][0]["reveal"] = None
        path.write_text(json.dumps(body))
        checked = check_step(load(path).current)
        assert "cannot be opened (no reveal)" in checked.reason
    def test_the_two_reasons_read_differently(self, tmp_path: Path) -> None:
        gap = check_step(load(written(tmp_path, unopened=1)).seek(4))
        forged = check_step(load(sealed_log(tmp_path, corrupt=1)).seek(1))
        assert "cannot be opened" in gap.reason
        assert "cannot be opened" not in forged.reason
        assert str(gap) != str(forged)
