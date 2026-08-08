from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_replay")).items() if not k.startswith("__")})

class TestTheLogCanVerifyItself:
    def test_an_honest_step_re_derives(self, tmp_path: Path) -> None:
        replay = load(sealed_log(tmp_path))
        assert check_step(replay.current).verified
    def test_the_log_stores_what_was_sealed_not_what_was_sent(self, tmp_path: Path) -> None:
        stored = load(sealed_log(tmp_path)).current.reveal
        assert stored is not None
        assert set(stored) == {
            "state",
            "role",
            "move",
            "intent",
            "hint",
            "barrier_placed",
            "scent",
            "game_uid",
            "sub_game",
        }
        assert "timestamp" not in stored
    def test_every_step_of_an_honest_log_verifies(self, tmp_path: Path) -> None:
        replay = load(sealed_log(tmp_path, steps=5))
        assert all(check_step(step).verified for step in replay.steps)
    def test_an_edited_record_cannot_be_made_to_agree(self, tmp_path: Path) -> None:
        replay = load(sealed_log(tmp_path, corrupt=2))
        checked = check_step(replay.seek(2))
        assert not checked.verified
        assert "produces" in checked.reason
    def test_an_edited_digest_is_caught_too(self, tmp_path: Path) -> None:
        path = sealed_log(tmp_path)
        body = json.loads(path.read_text())
        body["steps"][0]["commit"] = "f" * 64
        path.write_text(json.dumps(body))
        assert not check_step(load(path).current).verified
    def test_a_swapped_nonce_is_caught(self, tmp_path: Path) -> None:
        path = sealed_log(tmp_path)
        body = json.loads(path.read_text())
        body["steps"][0]["nonce"] = f"{99:032x}"
        path.write_text(json.dumps(body))
        assert not check_step(load(path).current).verified
