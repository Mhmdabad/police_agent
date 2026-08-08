from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tamper_acceptance")).items() if not k.startswith("__")})

class TestTheSmallestPossibleAlterations:
    def test_one_flipped_character_in_a_commitment(self, tmp_path: Path) -> None:
        def edit(body: dict[str, Any]) -> None:
            digest = body["steps"][0]["commit"]
            body["steps"][0]["commit"] = ("0" if digest[0] != "0" else "1") + digest[1:]
        assert stamp_after(tmp_path, edit) is Stamp.TAMPERED
    def test_one_flipped_character_in_a_nonce(self, tmp_path: Path) -> None:
        def edit(body: dict[str, Any]) -> None:
            secret = body["steps"][0]["nonce"]
            body["steps"][0]["nonce"] = ("0" if secret[0] != "0" else "1") + secret[1:]
        assert stamp_after(tmp_path, edit) is Stamp.TAMPERED
    def test_one_trailing_space_in_a_hint(self, tmp_path: Path) -> None:
        def edit(body: dict[str, Any]) -> None:
            body["steps"][0]["reveal"]["hint"] += " "
        assert stamp_after(tmp_path, edit) is Stamp.TAMPERED
    def test_one_cell_of_the_barrier_set_moved_by_one(self, tmp_path: Path) -> None:
        def edit(body: dict[str, Any]) -> None:
            body["steps"][1]["reveal"]["state"]["barriers"][0][0] += 1
        assert stamp_after(tmp_path, edit) is Stamp.TAMPERED
