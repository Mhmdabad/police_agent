from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_verdict")).items() if not k.startswith("__")})

class TestAnAlterationHoweverSmall:
    def test_a_changed_move_is_tampered(self, tmp_path: Path) -> None:
        result = walk(load(sealed_log(tmp_path, corrupt=2)))
        assert result.stamp is Stamp.TAMPERED
        assert result.stamp.text == "TAMPERED"
        assert result.stamp.value == "red"
    def test_one_tampered_step_voids_the_match(self, tmp_path: Path) -> None:
        assert walk(load(sealed_log(tmp_path, corrupt=3))).void
    def test_a_single_flipped_character_in_a_digest_is_enough(self, tmp_path: Path) -> None:
        path = sealed_log(tmp_path)
        original = json.loads(path.read_text())["steps"][1]["commit"]
        flipped = ("0" if original[0] != "0" else "1") + original[1:]
        def edit(body: dict[str, Any]) -> None:
            body["steps"][1]["commit"] = flipped
        result = walk(load(hand_edited(path, edit)))
        assert result.stamp is Stamp.TAMPERED
        assert result.at_step == 2
    def test_a_swapped_nonce_is_tampered(self, tmp_path: Path) -> None:
        def edit(body: dict[str, Any]) -> None:
            body["steps"][0]["nonce"] = f"{99:032x}"
        result = walk(load(hand_edited(sealed_log(tmp_path), edit)))
        assert result.stamp is Stamp.TAMPERED
    def test_a_hint_reworded_after_the_fact_is_tampered(self, tmp_path: Path) -> None:
        def edit(body: dict[str, Any]) -> None:
            body["steps"][0]["reveal"]["hint"] = "step one"
        assert walk(load(hand_edited(sealed_log(tmp_path), edit))).void
    def test_the_finding_is_one_the_other_team_can_check(self, tmp_path: Path) -> None:
        result = walk(load(sealed_log(tmp_path, corrupt=2)))
        assert result.at_step == 2
        assert "produces" in result.reason
        assert "TAMPERED at step 2" in str(result)
