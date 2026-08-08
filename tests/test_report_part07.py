from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_report")).items() if not k.startswith("__")})

class TestTheResultFileOnDisk:
    def test_the_name_derives_from_the_game_id(self) -> None:
        assert report().filename == "result_uoh26-s82kma9e.json"
    def test_it_writes_and_reads_back(self, tmp_path: Path) -> None:
        path = report().write(tmp_path)
        assert json.loads(path.read_text()) == report().to_dict()
    def test_it_creates_the_directory(self, tmp_path: Path) -> None:
        assert report().write(tmp_path / "artefacts" / "deep").exists()
    def test_the_file_and_the_attachment_are_the_same_bytes(self, tmp_path: Path) -> None:
        written = report().write(tmp_path).read_bytes()
        mail = Message(report=report(), sender="cop@example.com").build()
        attached = next(mail.iter_attachments()).get_payload(decode=True)
        assert attached == written
    def test_the_bytes_are_stable_between_writes(self, tmp_path: Path) -> None:
        assert (
            report().write(tmp_path / "a").read_text() == report().write(tmp_path / "b").read_text()
        )
    def test_it_carries_the_game_uid(self, tmp_path: Path) -> None:
        body = json.loads(report(game_uid="u-0001").write(tmp_path).read_text())
        assert body["game_uid"] == "u-0001"
    def test_the_commit_hashes_and_token_total_survive_the_round_trip(self, tmp_path: Path) -> None:
        body = json.loads(report().write(tmp_path).read_text())
        assert [entry["commit_hash"] for entry in body["sub_games"]] == [f"{1:040x}", f"{2:040x}"]
        assert body["totals"]["total_tokens"] == 41_233
        assert len(body["repositories"]) == 4
