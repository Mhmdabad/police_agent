from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tamper_acceptance")).items() if not k.startswith("__")})

class TestItJudgesContentNotBytes:
    def test_reindented_json_still_stamps_clean(self, tmp_path: Path) -> None:
        path = honest_log(tmp_path)
        path.write_text(json.dumps(json.loads(path.read_text())))
        assert walk(load(path)).stamp is Stamp.VERIFIED_OK
    def test_reordered_keys_still_stamp_clean(self, tmp_path: Path) -> None:
        path = honest_log(tmp_path)
        body = json.loads(path.read_text())
        for row in body["steps"]:
            row["reveal"] = dict(reversed(list(row["reveal"].items())))
        path.write_text(json.dumps(body))
        assert walk(load(path)).stamp is Stamp.VERIFIED_OK
