from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_step_zero")).items() if not k.startswith("__")})

class TestTheCommitMustDescribeWhatRan:
    def test_a_clean_tree_is_reproducible(self, tmp_path: Path) -> None:
        found = provenance("0.1.0", "s82kma9e", 3, repo=repo(tmp_path))
        assert found.reproducible
        assert found.github_commit is not None
        assert not found.dirty
        assert "sub-game 3 at" in str(found)
    def test_uncommitted_changes_make_it_unreproducible(self, tmp_path: Path) -> None:
        found = provenance("0.1.0", "s82kma9e", 3, repo=repo(tmp_path, dirty=True))
        assert found.github_commit is not None
        assert found.dirty
        assert not found.reproducible
        assert "uncommitted changes" in str(found)
    def test_the_declaration_records_the_dirty_flag_rather_than_hiding_it(
        self, tmp_path: Path
    ) -> None:
        found = provenance("0.1.0", "s82kma9e", 1, repo=repo(tmp_path, dirty=True))
        assert found.to_dict()["working_tree_dirty"] is True
    def test_no_repository_is_a_real_state_not_a_failure(self, tmp_path: Path) -> None:
        found = provenance("0.1.0", "s82kma9e", 1, repo=tmp_path)
        assert found.github_commit is None
        assert not found.reproducible
        assert "no commit hash available" in str(found)
    def test_it_finds_this_repository_by_default(self) -> None:
        assert provenance("0.1.0", "s82kma9e", 1).github_commit is not None
