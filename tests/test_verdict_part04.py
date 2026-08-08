from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_verdict")).items() if not k.startswith("__")})

class TestUnverifiableIsNotAnAccusation:
    def test_a_log_with_no_nonces_yet_is_incomplete(self, tmp_path: Path) -> None:
        result = walk(load(sealed_log(tmp_path, unopened=4)))
        assert result.stamp is Stamp.INCOMPLETE
        assert result.stamp.text == "INCOMPLETE"
        assert not result.void
    def test_it_names_the_step_it_could_not_open(self, tmp_path: Path) -> None:
        result = walk(load(sealed_log(tmp_path, unopened=2)))
        assert (result.verified, result.at_step) == (2, 3)
        assert "cannot be opened (no nonce)" in result.reason
    def test_incomplete_is_not_an_acquittal(self, tmp_path: Path) -> None:
        path = sealed_log(tmp_path, corrupt=2)
        def edit(body: dict[str, Any]) -> None:
            body["steps"][1]["nonce"] = None
        result = walk(load(hand_edited(path, edit)))
        assert result.stamp is Stamp.INCOMPLETE
        assert not result.clean
    def test_a_gap_does_not_shield_a_later_forgery(self, tmp_path: Path) -> None:
        path = sealed_log(tmp_path, steps=6, corrupt=5)
        def edit(body: dict[str, Any]) -> None:
            body["steps"][1]["nonce"] = None
        result = walk(load(hand_edited(path, edit)))
        assert result.stamp is Stamp.TAMPERED
        assert result.at_step == 5
        assert result.unopened == (2,), "the gap is reported, not treated as the verdict"
    def test_tampering_outranks_a_gap_whichever_comes_first(self, tmp_path: Path) -> None:
        path = sealed_log(tmp_path, steps=6, corrupt=2, unopened=3)
        assert walk(load(path)).stamp is Stamp.TAMPERED
    def test_the_three_stamps_are_distinguishable_to_a_reader(self, tmp_path: Path) -> None:
        clean = walk(load(sealed_log(tmp_path)))
        forged = walk(load(sealed_log(tmp_path / "b", corrupt=1)))
        partial = walk(load(sealed_log(tmp_path / "c", unopened=1)))
        assert len({clean.stamp, forged.stamp, partial.stamp}) == 3
        assert len({str(clean), str(forged), str(partial)}) == 3
